# 🚀 E2B + MCP Implementation TODO

Based on [E2B Cookbook: mcp-groq-exa-js](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/mcp-groq-exa-js)

---

## Phase 1: Setup (30 minutes)

### 1.1 Install Dependencies
```bash
cd /Users/sakethbachu/Documents/home/chatgpt-qa-agent
npm install e2b openai
```

### 1.2 Get API Keys
- [ ] E2B API Key: https://e2b.dev
- [ ] OpenAI API Key: platform.openai.com (or use existing)
- [ ] Exa API Key: https://exa.ai

### 1.3 Update Environment
Add to `.env`:
```env
E2B_API_KEY=your_e2b_api_key
OPENAI_API_KEY=sk-your_openai_key
EXA_API_KEY=your_exa_api_key
PORT=3001
NUM_QUESTIONS=3
NUM_ANSWERS=3
```

---

## Phase 2: Dynamic Question Generation (1 hour)

### 2.1 Create Question Generator Service
**File:** `src/services/questionGenerator.ts`

```typescript
import OpenAI from 'openai';

interface Question {
  id: string;
  text: string;
  answers: string[];
}

export async function generateQuestions(
  userQuery: string,
  numQuestions: number = 3,
  numAnswers: number = 3
): Promise<Question[]> {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  });

  const prompt = `Given this user request: "${userQuery}"

Generate ${numQuestions} multiple choice questions to understand their preferences better.
Each question should have ${numAnswers} answer options.

Return ONLY valid JSON in this exact format:
{
  "questions": [
    {
      "id": "q1",
      "text": "Question text here?",
      "answers": ["Option 1", "Option 2", "Option 3"]
    }
  ]
}`;

  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }],
    response_format: { type: "json_object" },
    temperature: 0.7
  });

  const result = JSON.parse(response.choices[0].message.content!);
  return result.questions;
}
```

### 2.2 Update Server to Use Dynamic Questions
**File:** `src/server.ts`

```typescript
import { generateQuestions } from './services/questionGenerator.js';

// In get-recommendation tool:
server.registerTool(
  "get-recommendation",
  {
    title: "AI-Powered Product Recommendations",
    description: "Get personalized recommendations with dynamic Q&A",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "What to recommend (e.g., 'chinos for work', 'action movies')"
        }
      },
      required: ["query"]
    },
    _meta: {
      "openai/outputTemplate": "ui://widget/qa.html",
    },
  },
  async (args: { [key: string]: any }) => {
    const query = args.query as string || 'product';
    const sessionId = generateSessionId();
    
    console.log(`Generating dynamic questions for: "${query}"`);
    
    // Generate questions dynamically
    const questions = await generateQuestions(query, NUM_QUESTIONS, NUM_ANSWERS);
    
    console.log('Generated questions:', questions);
    
    // Store in session
    userSessions.set(sessionId, {
      currentQuestionIndex: 0,
      answers: {},
      originalQuery: query,
      questions: questions
    });

    return {
      content: [
        {
          type: "text" as const,
          text: `I've generated ${questions.length} questions to understand your preferences for: "${query}"`,
        },
      ],
    };
  }
);
```

---

## Phase 3: E2B + MCP Integration (2-3 hours)

### 3.1 Create E2B Search Service
**File:** `src/services/e2bSearchService.ts`

```typescript
import Sandbox from 'e2b';
import OpenAI from 'openai';

interface SearchRequest {
  originalQuery: string;
  answers: Record<string, string>;
}

interface SearchResult {
  success: boolean;
  recommendations: string;
  error?: string;
}

export async function searchWithE2B(request: SearchRequest): Promise<SearchResult> {
  console.log('🚀 Creating E2B sandbox with Exa MCP server...');
  
  let sandbox: Sandbox | undefined;
  
  try {
    // 1. Create E2B sandbox with Exa MCP
    sandbox = await Sandbox.create({
      mcp: {
        exa: {
          apiKey: process.env.EXA_API_KEY!,
        },
      },
      timeoutMs: 600_000, // 10 minutes
    });

    console.log('✅ Sandbox created');
    console.log('📍 MCP URL:', sandbox.getMcpUrl());

    // 2. Create OpenAI client
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY!
    });

    // 3. Build search prompt
    const searchPrompt = buildSearchPrompt(request);
    console.log('🔍 Starting AI-powered search...');

    // 4. Call OpenAI with MCP tools
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a helpful recommendation assistant. Use the Exa search tool to find relevant products/items on the web. Provide specific recommendations with URLs, prices (if available), and explanations."
        },
        {
          role: "user",
          content: searchPrompt
        }
      ],
      tools: [
        {
          type: 'mcp' as any,
          server_label: 'e2b-mcp-gateway',
          server_url: sandbox.getMcpUrl(),
          headers: {
            'Authorization': `Bearer ${await sandbox.getMcpToken()}`
          }
        }
      ]
    });

    console.log('✅ Search complete!');

    return {
      success: true,
      recommendations: response.choices[0].message.content || 'No results found'
    };

  } catch (error: any) {
    console.error('❌ E2B search failed:', error);
    return {
      success: false,
      recommendations: '',
      error: error.message || 'Search failed'
    };
  } finally {
    // 5. Always cleanup sandbox
    if (sandbox) {
      console.log('🧹 Cleaning up sandbox...');
      await sandbox.kill();
      console.log('✅ Sandbox closed');
    }
  }
}

function buildSearchPrompt(request: SearchRequest): string {
  const { originalQuery, answers } = request;
  
  const preferences = Object.entries(answers)
    .map(([question, answer]) => `- ${question}: ${answer}`)
    .join('\n');

  return `Find the best recommendations for: "${originalQuery}"

User preferences:
${preferences}

Task:
1. Use the Exa search tool to find relevant products/items
2. Search multiple times if needed to get comprehensive results
3. Return your top 5-10 recommendations
4. For each recommendation include:
   - Name/Title
   - URL (if available)
   - Price (if available)
   - Why it matches the user's preferences
   - Brief description

Format your response in a clear, easy-to-read way.`;
}
```

---

## Phase 4: Wire Everything Together (1 hour)

### 4.1 Update Types
**File:** `src/types/session.types.ts`

```typescript
export interface Question {
  id: string;
  text: string;
  answers: string[];
}

export interface SessionData {
  currentQuestionIndex: number;
  answers: Record<string, string>;
  originalQuery: string;
  questions: Question[];
  searchResults?: any;
}
```

### 4.2 Update Submit Handler
**File:** `src/server.ts`

```typescript
import { searchWithE2B } from './services/e2bSearchService.js';

// Update /submit-answers endpoint
app.post("/submit-answers", async (req, res) => {
  const { sessionId, answers } = req.body;
  
  console.log('📨 Received answer submission:', { sessionId, answerCount: Object.keys(answers).length });
  
  const session = userSessions.get(sessionId);
  if (!session) {
    console.error('❌ Session not found:', sessionId);
    return res.status(404).json({ 
      success: false, 
      error: 'Session not found' 
    });
  }

  try {
    console.log('🔍 Starting E2B search...');
    console.log('Query:', session.originalQuery);
    console.log('Answers:', answers);

    // Use E2B + MCP to search
    const result = await searchWithE2B({
      originalQuery: session.originalQuery,
      answers: answers
    });

    if (result.success) {
      console.log('✅ Search successful!');
      session.searchResults = result.recommendations;
      
      res.json({
        success: true,
        message: 'Recommendations generated!',
        recommendations: result.recommendations
      });
    } else {
      console.error('❌ Search failed:', result.error);
      res.status(500).json({
        success: false,
        error: result.error || 'Search failed'
      });
    }
  } catch (error: any) {
    console.error('❌ Fatal error in submit handler:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to process answers'
    });
  }
});
```

### 4.3 Update Widget to Show Results
**File:** `src/server.ts` (in generateQAWidget function)

Update the `submitAnswers` function in the widget JavaScript:

```javascript
async function submitAnswers() {
  console.log('Submitting answers:', selectedAnswers);
  submitButton.disabled = true;
  submitButton.textContent = '🔍 Searching...';

  try {
    const response = await fetch('/submit-answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: '${sessionId}',
        answers: selectedAnswers
      })
    });

    const result = await response.json();
    
    if (result.success) {
      // Show results
      summaryBox.innerHTML = `
        <h3 style="color: #7c3aed; margin-bottom: 15px;">✨ Recommendations</h3>
        <div style="background: white; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto;">
          <pre style="white-space: pre-wrap; font-family: inherit;">${result.recommendations}</pre>
        </div>
      `;
      submitButton.style.display = 'none';
    } else {
      summaryBox.innerHTML += `
        <div style="background: #fee; padding: 10px; border-radius: 5px; margin-top: 10px; color: #c00;">
          ❌ Error: ${result.error}
        </div>
      `;
      submitButton.disabled = false;
      submitButton.textContent = 'Retry';
    }
  } catch (error) {
    console.error('Submit failed:', error);
    summaryBox.innerHTML += `
      <div style="background: #fee; padding: 10px; border-radius: 5px; margin-top: 10px; color: #c00;">
        ❌ Failed to submit answers. Please try again.
      </div>
    `;
    submitButton.disabled = false;
    submitButton.textContent = 'Retry';
  }
}
```

---

## Phase 5: Testing (1 hour)

### 5.1 Build and Start Server
```bash
npm run build
npm start
```

### 5.2 Ensure Ngrok is Running
```bash
ngrok http 3001 --log=stdout
```

### 5.3 Test Flow in ChatGPT
1. Use the action: "Use the recommendation tool for chinos for work"
2. Answer the dynamically generated questions
3. Click "Submit Answers"
4. Wait for E2B search (5-10 seconds)
5. Verify recommendations appear

### 5.4 Check Logs
Monitor for:
- ✅ Questions generated
- ✅ E2B sandbox created
- ✅ MCP URL obtained
- ✅ OpenAI called with MCP tools
- ✅ Search results returned
- ✅ Sandbox cleaned up

### 5.5 Test Different Queries
- [ ] "Recommend me chinos for work"
- [ ] "Recommend me action movies"
- [ ] "Recommend me laptops for coding"
- [ ] "Recommend me restaurants in SF"

---

## Phase 6: Error Handling & Polish (30 min)

### 6.1 Add Retry Logic
```typescript
async function searchWithRetry(request: SearchRequest, maxRetries = 2) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await searchWithE2B(request);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      console.log(`Retry ${i + 1}/${maxRetries}...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### 6.2 Add Timeout Protection
```typescript
async function searchWithTimeout(request: SearchRequest, timeoutMs = 30000) {
  return Promise.race([
    searchWithE2B(request),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Search timeout')), timeoutMs)
    )
  ]);
}
```

### 6.3 Add Loading Indicators
Update widget to show:
- "🤔 Generating questions..." (Phase 1)
- "🔍 Searching the web..." (Phase 2)
- "🤖 Analyzing results..." (Phase 3)
- "✨ Done!" (Phase 4)

---

## Phase 7: Documentation (30 min)

### 7.1 Update README
Add sections:
- E2B Setup
- Exa API Setup
- How Dynamic Q&A Works
- Architecture Diagram

### 7.2 Add Comments
Document key functions:
- `generateQuestions()`
- `searchWithE2B()`
- `buildSearchPrompt()`

---

## 📊 Summary

| Phase | Time | Status |
|-------|------|--------|
| 1. Setup | 30 min | ⏳ Pending |
| 2. Question Generation | 1 hour | ⏳ Pending |
| 3. E2B Integration | 2-3 hours | ⏳ Pending |
| 4. Wire Together | 1 hour | ⏳ Pending |
| 5. Testing | 1 hour | ⏳ Pending |
| 6. Error Handling | 30 min | ⏳ Pending |
| 7. Documentation | 30 min | ⏳ Pending |
| **Total** | **6-7 hours** | |

---

## 🚀 Ready to Start!

**First Command:**
```bash
cd /Users/sakethbachu/Documents/home/chatgpt-qa-agent
npm install e2b openai
```

**Then get API keys from:**
1. https://e2b.dev
2. https://exa.ai
3. platform.openai.com (if needed)

Let's build! 💪

