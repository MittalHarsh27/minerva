# 🎯 E2B + MCP Integration - Based on Real Example

## 📚 Reference

**Example:** [e2b-cookbook/mcp-groq-exa-js](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/mcp-groq-exa-js)

This example shows **exactly** what we need: E2B Sandbox + MCP + LLM + Search API!

## 🔍 How The Example Works

### Architecture Flow:
```
User Query
    ↓
E2B Sandbox (with Exa MCP Server)
    ├─ Groq LLM Client
    ├─ Exa MCP Server (for web search)
    └─ LLM calls Exa via MCP protocol
    ↓
Search Results
```

### Key Code Breakdown:

```typescript
// 1. Create E2B sandbox WITH Exa MCP server
const sandbox = await Sandbox.create({
  mcp: {
    exa: {
      apiKey: process.env.EXA_API_KEY,  // Exa API key
    },
  },
  timeoutMs: 600_000,  // 10 minutes
});

// 2. Create Groq client (LLM)
const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
});

// 3. Call LLM with MCP tools
const response = await client.responses.create({
  model: "moonshot/ai/kimi-k2-instruct-0905",
  input: researchPrompt,
  tools: [
    {
      type: 'mcp',
      server_label: 'e2b-mcp-gateway',  // MCP server
      server_url: sandbox.getMcpUrl(),  // E2B provides MCP endpoint!
      headers: {
        'Authorization': `Bearer ${await sandbox.getMcpToken()}`
      }
    }
  ]
});

// 4. LLM automatically calls Exa via MCP
// No manual API calls needed!
// Exa MCP server handles all search queries

// 5. Cleanup
await sandbox.kill();
```

## 🚀 Why This Changes Everything

### Before (What I Initially Thought):
```
Our Server → OpenAI API → Format Query → Exa API → Results
```
- Manual API orchestration
- We handle all API calls
- Simple but limited

### After (What E2B Example Shows):
```
E2B Sandbox:
  ├─ Exa MCP Server (handles search automatically)
  ├─ LLM (Groq/OpenAI)
  └─ LLM + MCP Protocol = Magic!
     (LLM decides when to search, what to search)
```
- LLM automatically calls search when needed
- MCP protocol handles communication
- Much more powerful!

## 💡 Key Advantages of E2B + MCP

### 1. **LLM-Driven Search**
The LLM decides WHEN and WHAT to search:
```typescript
User: "Recommend me chinos for work"

LLM thinks: "I need to search for work chinos"
  ↓
LLM calls Exa MCP: search("business casual chinos men")
  ↓
Gets results
  ↓
LLM thinks: "Let me refine with their preferences"
  ↓
LLM calls Exa MCP again: search("slim fit khaki chinos $50-100")
  ↓
Returns refined results
```

**Without E2B:** We manually format ONE search query
**With E2B:** LLM can make MULTIPLE intelligent searches!

### 2. **MCP Gateway Built-In**
E2B provides:
- `sandbox.getMcpUrl()` - Get MCP endpoint
- `sandbox.getMcpToken()` - Get auth token
- Automatic MCP server management

### 3. **Multiple MCP Servers**
Can add multiple services:
```typescript
const sandbox = await Sandbox.create({
  mcp: {
    exa: { apiKey: EXA_KEY },        // Web search
    filesystem: {},                   // File operations
    browserbase: { apiKey: BB_KEY },  // Browser automation
    // Add more...
  }
});
```

### 4. **Isolation & Security**
- Each user gets their own sandbox
- API keys stored securely
- Automatic cleanup

## 🎯 Updated Architecture for Our Project

### New Architecture: E2B + MCP + ChatGPT

```
┌──────────────┐
│   ChatGPT    │  User: "Recommend me chinos"
│    Widget    │
└───────┬──────┘
        │
        ↓
┌──────────────┐
│   Our MCP    │  1. Receive request
│    Server    │  2. Generate questions (OpenAI)
│  (Node.js)   │  3. User answers
└───────┬──────┘
        │
        ↓ Spawn E2B Sandbox
┌──────────────┐
│ E2B Sandbox  │
│              │
│  ┌─────────┐ │
│  │   Exa   │ │  • Web search MCP server
│  │   MCP   │ │  • Handles search queries
│  └─────────┘ │
│              │
│  ┌─────────┐ │
│  │  OpenAI │ │  • LLM for intelligence
│  │   LLM   │ │  • Calls Exa MCP when needed
│  └─────────┘ │  • Generates recommendations
│              │
└───────┬──────┘
        │
        ↓
┌──────────────┐
│   Results    │  • Intelligent search
│ + Reasoning  │  • Multiple queries if needed
└──────────────┘  • Formatted recommendations
```

## 📋 What We Need to Build

### Our MCP Server (Node.js):
1. ✅ Accept recommendation requests (already have)
2. ✅ Generate dynamic questions with OpenAI
3. ✅ Display widget with questions
4. ✅ Receive user answers
5. ✅ NEW: Spawn E2B sandbox
6. ✅ NEW: Pass answers to sandbox
7. ✅ NEW: Get results from sandbox
8. ✅ Return to ChatGPT

### Inside E2B Sandbox (TypeScript):
1. Receive user query + answers
2. Create Exa MCP server
3. Create OpenAI client
4. Generate prompt with user preferences
5. Let LLM + MCP do their magic
6. Return formatted results

## 🔑 API Keys Needed

1. **OpenAI API Key** - For question generation AND search reasoning
2. **Exa API Key** - For web search (via MCP)
3. **E2B API Key** - For sandboxes
4. ~~Groq API Key~~ - Optional (example uses Groq, we can use OpenAI)

## 💰 Cost Analysis

### Per User Interaction:

**Question Generation:**
- OpenAI GPT-4: ~$0.01

**E2B Sandbox:**
- Sandbox runtime (1-2 min): ~$0.02
- MCP Gateway: Included

**Search via MCP:**
- Exa searches (2-3 queries): ~$0.20-0.30
- LLM reasoning between searches: ~$0.03

**Total per interaction:** ~$0.26-0.35

**Worth it?** YES! Because:
- LLM makes intelligent, multiple searches
- Much better results than single search
- Automated reasoning and ranking
- Professional quality recommendations

## ⚡ Performance

### Timeline:
1. Question generation: 1-2s
2. User answers: [user time]
3. E2B sandbox spawn: ~0.5s
4. LLM + MCP search cycle: 3-5s
5. Results formatting: 0.5s

**Total (excluding user):** ~5-8 seconds

**Trade-off:** Slightly slower but MUCH smarter results!

## 🎨 Example Flow

### Input:
```
User: "Recommend me chinos for work"

Questions Generated:
1. Work environment? → Business casual
2. Preferred fit? → Slim fit  
3. Budget? → $50-$100
```

### Inside E2B Sandbox:
```typescript
// LLM receives context
const context = `
User wants: chinos for work
Preferences:
- Business casual environment
- Slim fit
- Budget: $50-$100
`;

// LLM + MCP magic happens:

// LLM thinks: "Let me search for general options first"
→ Calls Exa MCP: search("business casual chinos men 2024")
→ Gets 10 results

// LLM thinks: "Now let me narrow down by fit and price"
→ Calls Exa MCP: search("slim fit chinos $50-$100 business")
→ Gets 8 results

// LLM thinks: "Let me check reviews for top options"
→ Calls Exa MCP: search("best slim chinos reviews business casual")
→ Gets 5 results

// LLM synthesizes all results
→ Returns top 5 recommendations with reasoning
```

### Output:
```
🎯 Top Recommendations for Business Casual Chinos:

1. **Banana Republic Aiden Slim-Fit** ($89)
   ✓ Perfect for business casual
   ✓ Slim fit as requested
   ✓ Within budget
   ⭐ 4.5/5 stars (based on search results)
   
2. **J.Crew 770 Straight-Fit** ($79)
   ✓ Versatile for office wear
   ✓ Slightly relaxed slim fit
   ✓ Great value
   ⭐ 4.3/5 stars

[... more results]

📊 Why these? I searched current listings, compared prices 
in your range, and prioritized business-appropriate styles.
```

## 🚀 Implementation Strategy

### Phase 1: Basic E2B Integration
1. Set up E2B account + API key
2. Create simple sandbox test
3. Test Exa MCP server
4. Test LLM + MCP communication

### Phase 2: Integrate with Our Server
1. Add E2B SDK to our project
2. Create sandbox spawning logic
3. Pass user context to sandbox
4. Handle results

### Phase 3: Polish
1. Error handling
2. Timeout management
3. Cost optimization
4. Result formatting

## 🎯 Key Decision: Use E2B? YES!

### Reasons to Use E2B NOW:

1. ✅ **Perfect Example Exists**
   - We have working code to follow
   - Proven pattern for MCP + LLM + Search
   
2. ✅ **Much Smarter Results**
   - LLM-driven multi-query search
   - Intelligent ranking and synthesis
   - Better than simple API call

3. ✅ **Clean Architecture**
   - Separation of concerns
   - Scalable and maintainable
   - Professional approach

4. ✅ **Future-Proof**
   - Can add more MCP servers easily
   - Can add data analysis later
   - Can add visualizations

### Trade-offs Accepted:

- ❌ Slightly more complex
- ❌ ~$0.15 more per interaction
- ❌ ~2-3 seconds slower
- ✅ BUT: Much better quality!

## 📝 Conclusion

**Decision: YES, use E2B with MCP pattern!**

**Why:** The example shows this is the RIGHT way to build AI-powered search with intelligent reasoning. The extra cost and complexity are worth it for significantly better results.

**Next:** Update TODO with E2B implementation plan based on the cookbook example.

