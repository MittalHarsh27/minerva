# 📋 Dynamic Q&A with E2B + MCP - Implementation TODO

## 🎯 Goal
Transform our static Q&A agent into a dynamic, intelligent recommendation system using:
- **E2B Sandbox** for isolated execution
- **MCP Protocol** for tool integration  
- **Exa API** for intelligent web search
- **OpenAI API** for question generation AND search reasoning

## 📚 Based On
[E2B Cookbook: mcp-groq-exa-js Example](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/mcp-groq-exa-js)

---

## ✅ Phase 1: Setup & Environment (30 min)

### 1.1 Install E2B Dependencies
- [ ] Add `@e2b/code-interpreter` to package.json
- [ ] Add `openai` SDK (if not already present)
- [ ] Run `npm install`
- [ ] Verify installation

### 1.2 API Keys Configuration
- [ ] Get E2B API key from https://e2b.dev
- [ ] Get Exa API key from https://exa.ai
- [ ] Already have OpenAI API key
- [ ] Update `.env` file with:
  ```bash
  E2B_API_KEY=your_e2b_key
  EXA_API_KEY=your_exa_key
  OPENAI_API_KEY=your_openai_key
  PORT=3001
  NUM_QUESTIONS=3
  NUM_ANSWERS=3
  ```
- [ ] Update `.env.template` for documentation
- [ ] Test API keys with simple calls

### 1.3 Create E2B Sandbox Script
- [ ] Create `src/sandbox/researcher.ts`
  - This will run INSIDE the E2B sandbox
  - Handles: LLM + Exa MCP integration
  - Based on the cookbook example

---

## ✅ Phase 2: Question Generation (Already Mostly Done) (1 hour)

### 2.1 Update Question Generator
- [ ] Create `src/generators/questionGenerator.ts`
- [ ] Function: `generateQuestions(userQuery: string)`
  - Input: Original user query (e.g., "Recommend me chinos")
  - Output: Array of { question, options[] }
  - Use OpenAI API to generate contextually relevant questions

**Example Implementation:**
```typescript
async function generateQuestions(userQuery: string) {
  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      {
        role: "system",
        content: `You are a recommendation assistant. Given a user query 
        asking for product recommendations, generate ${NUM_QUESTIONS} 
        clarifying questions with ${NUM_ANSWERS} options each. Return JSON.`
      },
      {
        role: "user",
        content: userQuery
      }
    ],
    response_format: { type: "json_object" }
  });
  
  return JSON.parse(response.choices[0].message.content);
}
```

### 2.2 Update get-recommendation Tool
- [ ] Modify `src/server.ts` → `get-recommendation` handler
- [ ] Call `generateQuestions()` instead of static questions
- [ ] Store original query in session
- [ ] Generate widget HTML with dynamic questions
- [ ] Return widget to ChatGPT

---

## ✅ Phase 3: E2B Sandbox Integration (2 hours)

### 3.1 Create Sandbox Researcher Script

**File:** `src/sandbox/researcher.ts`

This runs INSIDE the E2B sandbox!

```typescript
import Sandbox from 'e2b';
import { OpenAI } from 'openai';

interface ResearchRequest {
  originalQuery: string;
  answers: Record<string, string>;
}

async function runResearch(request: ResearchRequest) {
  console.log('Creating E2B sandbox with Exa MCP server...');
  
  // Create sandbox with Exa MCP
  const sandbox = await Sandbox.create({
    mcp: {
      exa: {
        apiKey: process.env.EXA_API_KEY!,
      },
    },
    timeoutMs: 600_000, // 10 minutes
  });

  try {
    console.log('Sandbox created:', sandbox.getMcpUrl());

    // Create OpenAI client
    const client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY!,
    });

    // Build research prompt with user context
    const researchPrompt = buildResearchPrompt(request);

    console.log('Starting AI research...');

    // Call LLM with MCP tools
    const response = await client.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a research assistant. Use the Exa search tool to find relevant recommendations."
        },
        {
          role: "user",
          content: researchPrompt
        }
      ],
      tools: [
        {
          type: 'mcp',
          server_label: 'e2b-mcp-gateway',
          server_url: sandbox.getMcpUrl(),
          headers: {
            'Authorization': `Bearer ${await sandbox.getMcpToken()}`
          }
        }
      ]
    });

    console.log('Research complete!');
    
    return {
      success: true,
      results: response.choices[0].message.content,
      reasoning: "Used Exa search via MCP"
    };

  } finally {
    // Always cleanup
    console.log('Cleaning up sandbox...');
    await sandbox.kill();
    console.log('Sandbox closed');
  }
}

function buildResearchPrompt(request: ResearchRequest): string {
  const { originalQuery, answers } = request;
  
  return `
User Query: ${originalQuery}

User Preferences:
${Object.entries(answers).map(([q, a]) => `- ${q}: ${a}`).join('\n')}

Task: Use the Exa search tool to find the best recommendations based on these preferences. 
Search multiple times if needed to refine results. Return your top 5 recommendations 
with explanations and links.
`;
}

// Export for use
export { runResearch };
```

**Tasks:**
- [ ] Create `src/sandbox/` directory
- [ ] Create `researcher.ts` with above code
- [ ] Add proper TypeScript types
- [ ] Add error handling
- [ ] Add logging

### 3.2 Integrate Sandbox into Main Server

**Update:** `src/server.ts`

```typescript
import { runResearch } from './sandbox/researcher.js';

// In process-answers or submit-answers handler:
async function handleAnswerSubmission(sessionId: string, answers: Record<string, string>) {
  const session = userSessions.get(sessionId);
  if (!session) {
    return { error: 'Session not found' };
  }

  console.log('Spawning E2B sandbox for research...');
  
  try {
    // Run research in E2B sandbox
    const results = await runResearch({
      originalQuery: session.originalQuery,
      answers: answers
    });

    console.log('Research results:', results);

    // Store results in session
    session.searchResults = results;

    // Return formatted results
    return {
      success: true,
      message: 'Research complete!',
      recommendations: results.results
    };

  } catch (error) {
    console.error('E2B research failed:', error);
    return {
      success: false,
      error: 'Failed to generate recommendations'
    };
  }
}
```

**Tasks:**
- [ ] Import researcher module
- [ ] Update `/submit-answers` endpoint
- [ ] Add error handling for sandbox failures
- [ ] Add timeout handling
- [ ] Log all steps for debugging

---

## ✅ Phase 4: Testing & Validation (1 hour)

### 4.1 Unit Tests
- [ ] Test question generation
  - Input: "Recommend me movies"
  - Expected: 3 questions about genre, language, etc.
- [ ] Test E2B sandbox creation
  - Verify MCP URL is returned
  - Verify token is valid
- [ ] Test research function
  - Mock answers
  - Verify search results are returned

### 4.2 Integration Tests
- [ ] End-to-end flow:
  1. User sends query: "Recommend me chinos"
  2. Questions generated
  3. User answers questions
  4. E2B sandbox spawned
  5. LLM + MCP search executed
  6. Results returned
- [ ] Test with different queries:
  - Products: chinos, laptops, phones
  - Entertainment: movies, books, games
  - Services: restaurants, hotels

### 4.3 Error Scenarios
- [ ] Invalid API keys
- [ ] Sandbox timeout
- [ ] Network failures
- [ ] Malformed user input

---

## ✅ Phase 5: UI Updates (30 min)

### 5.1 Update Widget HTML
- [ ] Add loading state while sandbox runs
- [ ] Show progress: "Searching...", "Analyzing...", "Generating..."
- [ ] Display results in nice format
- [ ] Add links to search results

**Example:**
```html
<div id="loading" style="display:none;">
  <div class="spinner"></div>
  <p>🔍 Searching the web for the best options...</p>
  <p>🤔 Analyzing results...</p>
  <p>✨ Generating recommendations...</p>
</div>

<div id="results" style="display:none;">
  <h3>🎯 Top Recommendations</h3>
  <div class="recommendation-list">
    <!-- Results will be inserted here -->
  </div>
</div>
```

### 5.2 Update Submit Handler
- [ ] Show loading state on submit
- [ ] Poll server for results (if async)
- [ ] Display results when ready
- [ ] Handle errors gracefully

---

## ✅ Phase 6: Documentation (30 min)

### 6.1 Update README.md
- [ ] Add E2B setup instructions
- [ ] Add Exa API setup
- [ ] Update environment variables section
- [ ] Add architecture diagram
- [ ] Add example flows

### 6.2 Add Code Comments
- [ ] Document researcher.ts
- [ ] Document question generation logic
- [ ] Document MCP integration
- [ ] Add inline comments for complex logic

### 6.3 Create Usage Examples
- [ ] Add example queries
- [ ] Add expected outputs
- [ ] Add troubleshooting guide

---

## ✅ Phase 7: Optimization (1 hour)

### 7.1 Performance
- [ ] Cache question generation for similar queries
- [ ] Reuse sandbox if possible
- [ ] Optimize prompt size
- [ ] Reduce API calls where possible

### 7.2 Cost Management
- [ ] Add usage tracking
- [ ] Set budget limits
- [ ] Log API costs
- [ ] Alert on high usage

### 7.3 Error Recovery
- [ ] Retry logic for API failures
- [ ] Fallback to simple search if E2B fails
- [ ] Graceful degradation

---

## 📊 Phase Summary

| Phase | Time | Complexity | Priority |
|-------|------|------------|----------|
| 1. Setup | 30 min | Low | 🔴 High |
| 2. Questions | 1 hour | Medium | 🔴 High |
| 3. E2B Integration | 2 hours | High | 🔴 High |
| 4. Testing | 1 hour | Medium | 🟡 Medium |
| 5. UI Updates | 30 min | Low | 🟡 Medium |
| 6. Documentation | 30 min | Low | 🟢 Low |
| 7. Optimization | 1 hour | Medium | 🟢 Low |
| **Total** | **6.5 hours** | - | - |

---

## 🚀 Getting Started

**Immediate Next Steps:**

1. **Install E2B SDK:**
   ```bash
   cd /Users/sakethbachu/Documents/home/chatgpt-qa-agent
   npm install @e2b/code-interpreter openai
   ```

2. **Get API Keys:**
   - E2B: https://e2b.dev/docs/getting-started/api-key
   - Exa: https://dashboard.exa.ai/api-keys

3. **Create `.env` file:**
   ```bash
   cp .env.template .env
   # Add all API keys
   ```

4. **Test E2B connection:**
   ```bash
   npm run test:e2b
   ```

---

## ❓ Open Questions

1. **Sandbox Reuse:** Should we keep sandboxes alive between requests from same user?
   - Pro: Faster responses
   - Con: Higher costs
   - Decision: ?

2. **Search Depth:** How many search iterations should LLM make?
   - Current: Let LLM decide
   - Alternative: Set hard limit (e.g., max 3 searches)
   - Decision: ?

3. **Result Caching:** Should we cache search results?
   - Pro: Faster for similar queries
   - Con: Results might be outdated
   - Decision: ?

4. **Fallback Strategy:** What if E2B fails?
   - Option A: Return error to user
   - Option B: Fall back to simple OpenAI completion
   - Option C: Fall back to direct Exa API call
   - Decision: ?

---

## 📝 Notes

- The cookbook example uses Groq, but we can use OpenAI (we already have API key)
- E2B provides the MCP gateway automatically - we don't need to set it up ourselves
- The sandbox automatically handles cleanup, but we should add explicit cleanup in `finally` blocks
- Consider adding rate limiting to prevent abuse
- Monitor costs closely in first few days

---

## ✅ Ready to Start?

**Checklist before starting:**
- [ ] API keys ready
- [ ] Development environment set up
- [ ] Example code reviewed
- [ ] Architecture understood
- [ ] Questions answered

**Let's build! 🚀**

