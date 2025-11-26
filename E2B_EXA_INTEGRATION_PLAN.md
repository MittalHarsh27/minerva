# E2B + Exa + Python Integration Plan

## Overview
This document outlines the plan for integrating E2B sandbox with Exa AI search using Python, enabling complex search queries with code execution capabilities.

## Architecture

```
User Query + Answers
  ↓
Express.js (TypeScript)
  ↓ HTTP POST
Python FastAPI Service
  ↓
E2B Sandbox (Python)
  ├─ Exa MCP (Search)
  ├─ OpenAI (Query Processing)
  └─ Python Code (Filtering/Sorting)
  ↓
Search Results
  ↓
Return to User
```

## TODO List by Phase

### Phase 1: Setup & Configuration ⚙️

#### 1.1 Account Setup
- [ ] **setup-1**: Set up E2B account and get API key
  - Sign up at https://e2b.dev
  - Get $100 free credits
  - Copy API key to .env file

- [ ] **setup-2**: Get Exa AI API key
  - Sign up at https://exa.ai
  - Get $10 free credits
  - Copy API key to .env file

#### 1.2 Environment Configuration
- [ ] **setup-3**: Add API keys to .env file
  ```env
  E2B_API_KEY=your_e2b_key_here
  EXA_API_KEY=your_exa_key_here
  OPENAI_API_KEY=existing_key
  ```

#### 1.3 Dependencies
- [ ] **setup-4**: Install E2B Python SDK
  ```bash
  cd python-service
  pip install e2b
  ```

- [ ] **setup-5**: Update requirements.txt
  ```txt
  e2b>=0.1.0
  ```

---

### Phase 2: Core Search Service 🔍

#### 2.1 Create Search Service
- [ ] **service-1**: Create `python-service/services/search_service.py`
  - File structure for E2B + Exa integration
  - Import statements (e2b, openai, os)

- [ ] **service-2**: Implement `build_search_prompt()`
  - Takes: user_query, user_answers, user_id
  - Returns: formatted prompt string
  - Includes context about user preferences
  - Handles complex query types ("top 10", "I haven't bought")

- [ ] **service-3**: Implement `search_with_e2b_exa()`
  - Create E2B sandbox with Exa MCP
  - Configure MCP with Exa API key
  - Call OpenAI with MCP tools
  - Handle sandbox lifecycle (create → use → kill)
  - Error handling and cleanup

- [ ] **service-4**: Implement `parse_response()`
  - Extract search results from OpenAI response
  - Format results for frontend
  - Handle different response structures

- [ ] **service-5**: Add error handling and retry logic
  - E2B sandbox creation failures
  - Exa API failures
  - OpenAI API failures
  - Timeout handling
  - Retry with exponential backoff

---

### Phase 3: API Integration 🌐

#### 3.1 Data Models
- [ ] **api-1**: Create Pydantic models in `python-service/models/search.py`
  ```python
  class SearchRequest(BaseModel):
      query: str
      answers: dict
      user_id: Optional[str] = None
  
  class SearchResponse(BaseModel):
      success: bool
      results: List[dict]
      error: Optional[str] = None
  ```

#### 3.2 FastAPI Endpoint
- [ ] **api-2**: Add POST `/api/search` endpoint to `main.py`
  - Accept SearchRequest
  - Call search_with_e2b_exa()
  - Return SearchResponse
  - Error handling

- [ ] **api-3**: Update CORS configuration
  - Ensure Express.js can call search endpoint
  - Add to existing CORS middleware

---

### Phase 4: Express.js Integration 🔗

#### 4.1 Update Answer Endpoint
- [ ] **integration-1**: Modify `/api/answers` endpoint in `src/server.ts`
  - After saving answers, call Python search service
  - Pass: originalQuery, answers, userId
  - Handle search results

- [ ] **integration-2**: Add error handling
  - Python service unavailable
  - Search service errors
  - Fallback behavior

#### 4.2 Frontend Updates
- [ ] **integration-3**: Update frontend to display results
  - Show search results after answer submission
  - Display recommendations
  - Handle loading states
  - Error display

---

### Phase 5: Database Integration (Optional) 💾

#### 5.1 Database Schema
- [ ] **database-1**: Design schema for user history
  - Table: `user_purchases` (user_id, product_id, purchased_at)
  - Table: `user_watch_history` (user_id, product_id, watched_at)
  - Indexes for fast queries

#### 5.2 Database MCP (If Needed)
- [ ] **database-2**: Add database MCP to E2B sandbox
  - Only if complex queries need database access
  - Configure PostgreSQL/Supabase MCP
  - Test database queries in sandbox

---

### Phase 6: Testing 🧪

#### 6.1 Basic Testing
- [ ] **testing-1**: Test simple search queries
  - "Find me running shoes"
  - Verify Exa search works
  - Check result format

#### 6.2 Complex Testing
- [ ] **testing-2**: Test complex queries
  - "Top 10 running shoes"
  - "Shoes I haven't bought"
  - "Best laptops I didn't watch"
  - Verify filtering/sorting works

#### 6.3 Error Testing
- [ ] **testing-3**: Test error scenarios
  - E2B sandbox timeout
  - Exa API failure
  - Invalid queries
  - Network errors

---

### Phase 7: Optimization 🚀

#### 7.1 Query Classification
- [ ] **optimization-1**: Add query complexity detection
  - Simple queries → Direct Exa API (no sandbox)
  - Complex queries → E2B sandbox
  - Reduce costs for simple searches

#### 7.2 Caching
- [ ] **optimization-2**: Implement caching
  - Cache search results for repeated queries
  - Reduce E2B usage
  - Improve response time

#### 7.3 Monitoring
- [ ] **optimization-3**: Add logging and monitoring
  - Log E2B usage (sandbox time, costs)
  - Track search query patterns
  - Monitor error rates
  - Cost tracking

---

## File Structure

```
chatgpt-qa-agent/
├── .env                          # Add E2B_API_KEY, EXA_API_KEY
├── python-service/
│   ├── main.py                  # Add /api/search endpoint
│   ├── requirements.txt         # Add e2b dependency
│   ├── services/
│   │   ├── question_generator.py  # Existing
│   │   └── search_service.py      # NEW: E2B + Exa integration
│   └── models/
│       ├── question.py          # Existing
│       └── search.py             # NEW: Search request/response models
└── src/
    └── server.ts                # Update /api/answers endpoint
```

---

## Cost Estimates

### E2B Costs (per complex query)
- Sandbox creation: ~$0.001
- Runtime (3 min avg): ~$0.009
- **Total per query: ~$0.01**

### Exa Costs (per search)
- Search (1-25 results): $5 per 1,000 = $0.005 per search
- Contents (if needed): $1 per 1,000 pages

### Monthly Estimate (1,000 complex queries)
- E2B: 1,000 × $0.01 = $10/month
- Exa: 1,000 × $0.005 = $5/month
- **Total: ~$15/month** (within free credits initially)

---

## Implementation Order

1. **Start with Phase 1** (Setup) - 30 minutes
2. **Phase 2** (Core Service) - 2-3 hours
3. **Phase 3** (API) - 1 hour
4. **Phase 4** (Integration) - 1-2 hours
5. **Phase 5** (Database) - Optional, later
6. **Phase 6** (Testing) - Ongoing
7. **Phase 7** (Optimization) - After initial testing

---

## Success Criteria

✅ Simple searches work (direct Exa API)
✅ Complex searches work (E2B + Exa)
✅ Filtering works ("I haven't bought")
✅ Sorting works ("top 10")
✅ Error handling works
✅ Costs are reasonable (<$20/month for MVP)

---

## Next Steps

1. Review this plan
2. Start with Phase 1 (Setup)
3. Test each phase before moving to next
4. Monitor costs and optimize

