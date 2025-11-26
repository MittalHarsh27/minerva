# 🚀 E2B + MCP Implementation Plan

## 📚 Reference Example Analysis

**Source:** [E2B Cookbook - MCP Groq Exa Example](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/mcp-groq-exa-js)

### What the Example Shows

The example demonstrates a **perfect pattern** for our use case:

```typescript
// 1. Create E2B sandbox with Exa MCP server
const sandbox = await Sandbox.create({
  mcp: {
    exa: {
      apiKey: process.env.EXA_API_KEY,
    },
  },
  timeoutMs: 600_000, // 10 minutes
});

// 2. Create LLM client (Groq in example, we'll use OpenAI)
const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
});

// 3. Call LLM with MCP tools
const response = await client.responses.create({
  model: "moonshot/ai/kimi-k2-instruct-8k05",
  input: researchPrompt,
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

// 4. Get results and cleanup
console.log(response.output_text);
await sandbox.kill();
```

### Key Insights

1. ✅ **E2B handles MCP server automatically** - No need to set up Exa separately!
2. ✅ **LLM can call Exa via MCP** - The AI decides when to search
3. ✅ **Sandboxed execution** - Secure and isolated
4. ✅ **Simple API** - Much cleaner than we thought!

## 🎯 Our Adapted Architecture

### Updated Flow

```
User: "Recommend me chinos for work"
  ↓
ChatGPT Widget (Skybridge)
  ↓
Our MCP Server (Node.js)
  ↓
┌─────────────────────────────────────┐
│ 1. Generate Dynamic Questions       │
│    - Call OpenAI API directly       │
│    - "Based on 'chinos for work',   │
│      generate 3 questions..."       │
└────────────┬────────────────────────┘
             │
             ↓ (User answers questions)
┌─────────────────────────────────────┐
│ 2. Create E2B Sandbox with Exa MCP │
│    const sandbox = await            │
│    Sandbox.create({                 │
│      mcp: { exa: { apiKey } }       │
│    });                              │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 3. Call OpenAI with MCP Tools       │
│    - Pass user answers              │
│    - Let OpenAI search via Exa MCP  │
│    - OpenAI analyzes results        │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 4. Return Recommendations           │
│    - Format results                 │
│    - Display in ChatGPT             │
│    - Kill sandbox                   │
└─────────────────────────────────────┘
```

## 🔑 Required API Keys

1. **E2B API Key** - For sandbox creation
2. **OpenAI API Key** - For LLM calls & question generation
3. **Exa API Key** - Passed to E2B sandbox MCP server

## 📋 Updated TODO

### Phase 1: Setup & Basic Integration (2-3 hours)

#### TODO 1.1: Get API Keys ✅
- [x] E2B API Key (sign up at e2b.dev)
- [x] OpenAI API Key (platform.openai.com)
- [x] Exa API Key (exa.ai)

#### TODO 1.2: Install E2B SDK
```bash
npm install e2b @e2b/code-interpreter
npm install openai
npm install dotenv
```

#### TODO 1.3: Environment Setup
```env
E2B_API_KEY=your_e2b_key
OPENAI_API_KEY=sk-...
EXA_API_KEY=your_exa_key
```

### Phase 2: Question Generation (1 hour)

#### TODO 2.1: Create Question Generation Service
**File:** `src/services/questionGenerator.ts`

```typescript
import OpenAI from 'openai';

export async function generateQuestions(
  userQuery: string,
  numQuestions: number = 3
): Promise<Question[]> {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  });

  const prompt = `Given this user query: "${userQuery}"
  
  Generate ${numQuestions} multiple choice questions to understand their preferences.
  Each question should have 4 answer options.
  
  Return JSON: {
    "questions": [
      {
        "id": "q1",
        "text": "Question text?",
        "answers": ["Option 1", "Option 2", "Option 3", "Option 4"]
      }
    ]
  }`;

  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }],
    response_format: { type: "json_object" }
  });

  return JSON.parse(response.choices[0].message.content!).questions;
}
```

### Phase 3: E2B Sandbox Integration (2-3 hours)

#### TODO 3.1: Create E2B Search Service
**File:** `src/services/e2bSearchService.ts`

```typescript
import Sandbox from 'e2b';
import OpenAI from 'openai';

export async function searchWithE2B(
  userQuery: string,
  answers: Record<string, string>
): Promise<SearchResults> {
  console.log('Creating E2B sandbox with Exa MCP server...');
  
  // 1. Create sandbox with Exa MCP
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

    // 2. Create OpenAI client
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY!
    });

    // 3. Format search prompt with user answers
    const searchPrompt = formatSearchPrompt(userQuery, answers);

    // 4. Call OpenAI with MCP tools
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "user",
          content: searchPrompt
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

    // 5. Parse and return results
    return parseSearchResults(response);

  } finally {
    // 6. Always cleanup sandbox
    console.log('Cleaning up sandbox...');
    await sandbox.kill();
    console.log('Sandbox closed');
  }
}

function formatSearchPrompt(
  query: string,
  answers: Record<string, string>
): string {
  const prefs = Object.entries(answers)
    .map(([q, a]) => `${q}: ${a}`)
    .join('\n');

  return `Find products for: "${query}"

User preferences:
${prefs}

Use Exa to search the web for relevant products. Return:
1. Product name & URL
2. Price (if available)
3. Why it matches the user's preferences
4. Brief description

Find at least 5-10 good matches.`;
}
```

### Phase 4: Update MCP Server (1 hour)

#### TODO 4.1: Update get-recommendation Tool
```typescript
server.registerTool(
  "get-recommendation",
  {
    title: "AI-Powered Product Recommendations",
    description: "Dynamic Q&A with AI-powered web search",
    _meta: {
      "openai/outputTemplate": "ui://widget/qa.html",
    },
  },
  async (args: { [key: string]: any }) => {
    const query = args.query as string || 'product';
    const sessionId = generateSessionId();
    
    // Generate dynamic questions using OpenAI
    const questions = await generateQuestions(query, NUM_QUESTIONS);
    
    // Store session
    userSessions.set(sessionId, {
      currentQuestionIndex: 0,
      answers: {},
      originalQuery: query,
      questions: questions // Store generated questions
    });

    return {
      content: [
        {
          type: "text" as const,
          text: `I've generated personalized questions for: "${query}"`,
        },
      ],
    };
  }
);
```

#### TODO 4.2: Update process-answers Endpoint
```typescript
app.post("/submit-answers", async (req, res) => {
  const { sessionId, answers } = req.body;
  
  const session = userSessions.get(sessionId);
  if (!session) {
    return res.status(404).json({ error: 'Session not found' });
  }

  try {
    // Use E2B + MCP to search
    const results = await searchWithE2B(
      session.originalQuery,
      answers
    );

    res.json({
      success: true,
      results: results,
      message: 'Found recommendations!'
    });
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});
```

### Phase 5: Testing & Refinement (1-2 hours)

#### TODO 5.1: Test Complete Flow
```bash
# 1. Start server
npm start

# 2. Test in ChatGPT:
#    "Use the recommendation tool for chinos"

# 3. Answer questions

# 4. Click submit

# 5. Verify:
#    - E2B sandbox creates successfully
#    - OpenAI calls Exa via MCP
#    - Results are returned
#    - Sandbox cleans up
```

#### TODO 5.2: Monitor Sandbox Creation
```typescript
// Add logging
console.log('Sandbox status:', sandbox.getStatus());
console.log('MCP URL:', sandbox.getMcpUrl());
console.log('MCP Token:', await sandbox.getMcpToken());
```

#### TODO 5.3: Error Handling
```typescript
try {
  const sandbox = await Sandbox.create({ /* ... */ });
  // ... use sandbox
} catch (error) {
  if (error.code === 'RATE_LIMIT') {
    // Handle rate limit
  } else if (error.code === 'TIMEOUT') {
    // Handle timeout
  }
  throw error;
} finally {
  await sandbox?.kill();
}
```

## 📊 Project Structure

```
chatgpt-qa-agent/
├── src/
│   ├── server.ts                    # Main MCP server
│   ├── services/
│   │   ├── questionGenerator.ts     # NEW: OpenAI question generation
│   │   ├── e2bSearchService.ts      # NEW: E2B + Exa MCP integration
│   │   └── resultFormatter.ts       # NEW: Format search results
│   ├── types/
│   │   ├── question.types.ts        # Question interfaces
│   │   ├── search.types.ts          # Search result interfaces
│   │   └── session.types.ts         # Session with questions
│   └── utils/
│       ├── prompts.ts               # LLM prompt templates
│       └── sandbox.ts               # Sandbox management utilities
├── .env                             # API keys
├── package.json                     # Updated dependencies
└── README.md                        # Documentation
```

## 🎯 Key Differences from Original Plan

### What Changed:

1. **No separate Exa SDK needed** ✅
   - E2B provides Exa via MCP automatically
   - Simpler integration

2. **LLM decides when to search** ✅
   - OpenAI calls Exa tools as needed
   - More intelligent than hardcoded search

3. **Cleaner architecture** ✅
   - Less boilerplate code
   - E2B handles MCP complexity

4. **Better prompt engineering** ✅
   - Let OpenAI format its own search queries
   - More natural results

### What Stayed the Same:

1. ✅ Dynamic question generation (OpenAI)
2. ✅ User answers via widget
3. ✅ Search-based recommendations
4. ✅ Results displayed in ChatGPT

## 💰 Cost Estimate

### Per Query:
- **OpenAI (questions):** ~$0.002 (gpt-3.5-turbo)
- **OpenAI (search + analysis):** ~$0.01 (gpt-4)
- **E2B Sandbox:** ~$0.05 (estimated)
- **Exa searches:** ~$0.05-0.10 (depending on searches)

**Total:** ~$0.11-0.16 per complete recommendation

### Monthly (1000 queries):
- **Low estimate:** $110/month
- **High estimate:** $160/month

## ⚡ Performance

### Expected Times:
- Question generation: ~1-2 seconds
- Sandbox creation: ~150ms-500ms
- Search + analysis: ~3-5 seconds
- Sandbox cleanup: ~500ms

**Total:** ~5-8 seconds per complete flow

## 🚀 Implementation Order

1. **Phase 1:** Setup (30 min)
   - Get API keys
   - Install dependencies
   - Configure environment

2. **Phase 2:** Question Generation (1 hour)
   - Implement questionGenerator service
   - Test with different queries

3. **Phase 3:** E2B Integration (2-3 hours)
   - Implement e2bSearchService
   - Test sandbox creation
   - Test MCP tool usage

4. **Phase 4:** Update Server (1 hour)
   - Update MCP tools
   - Update endpoints
   - Wire everything together

5. **Phase 5:** Testing (1-2 hours)
   - End-to-end testing
   - Error handling
   - Performance optimization

**Total Time:** 5-7 hours

## 🎯 Success Criteria

### MVP Must Have:
- ✅ Dynamic questions generated by OpenAI
- ✅ User answers collected via widget
- ✅ E2B sandbox creates successfully
- ✅ OpenAI uses Exa MCP to search
- ✅ Results returned to ChatGPT
- ✅ Sandbox cleanup works

### Nice to Have:
- ✅ Caching common questions
- ✅ Parallel searches for different queries
- ✅ Rich result formatting
- ✅ Images/prices in results

## 📚 Resources

- [E2B Documentation](https://e2b.dev/docs)
- [E2B MCP Gateway](https://e2b.dev/docs/mcp)
- [Example Code](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/mcp-groq-exa-js)
- [Exa Documentation](https://docs.exa.ai)
- [Groq Documentation](https://console.groq.com/docs)

## ✅ Ready to Implement?

This plan leverages the exact pattern from E2B's official example but adapted for our use case. The architecture is:
- ✅ Proven (official example)
- ✅ Simpler than expected
- ✅ More powerful (LLM-driven search)
- ✅ Well-documented

**Let's proceed with implementation!** 🚀


