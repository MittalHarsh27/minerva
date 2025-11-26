# Retry Logic Placement Discussion

## 🎯 Question: Where Should Retry Logic Live?

When migrating API calling and validation to Python, we need to decide where retry logic lives.

---

## 📊 Current State

**Current (TypeScript):**
```typescript
export async function generateQuestions(...) {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const questions = await callOpenAI(...);  // API call
      const validated = QuestionsResponseSchema.parse({ questions });  // Validation
      return validated.questions;
    } catch (error) {
      if (attempt === MAX_RETRIES) {
        return STATIC_FALLBACK;  // Fallback
      }
      await sleep(exponential_backoff);
    }
  }
}
```

**Current retry logic:**
- Retries: 4 attempts
- Backoff: Exponential (1s, 2s, 4s)
- Scope: API call + validation
- Fallback: Static questions (in TypeScript)

---

## 🤔 Two Options

### Option A: Retry in TypeScript (HTTP Level)

**Architecture:**
```
TypeScript (generateQuestions)
  ├─ Attempt 1: HTTP call → Python service
  │   └─ Python: callOpenAI() + validation
  │       └─ Fails → TypeScript retries
  ├─ Attempt 2: HTTP call → Python service
  │   └─ Python: callOpenAI() + validation
  │       └─ Fails → TypeScript retries
  └─ Attempt 3: HTTP call → Python service
      └─ Python: callOpenAI() + validation
          └─ Success → Return questions
```

**TypeScript:**
```typescript
export async function generateQuestions(...) {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      // HTTP call to Python service
      const response = await fetch('http://localhost:8000/api/generate-questions', {
        method: 'POST',
        body: JSON.stringify({ userQuery, numQuestions, numAnswers })
      });
      
      if (!response.ok) throw new Error('Python service error');
      
      const data = await response.json();
      return data.questions;
    } catch (error) {
      if (attempt === MAX_RETRIES) {
        return STATIC_FALLBACK;
      }
      await sleep(exponential_backoff);
    }
  }
}
```

**Python:**
```python
@app.post("/api/generate-questions")
async def generate_questions(request: GenerateQuestionsRequest):
    # No retry logic - just one attempt
    questions = call_openai_with_validation(...)
    return {"questions": questions}
```

**Pros:**
- ✅ TypeScript controls retry strategy
- ✅ Can change retry logic without touching Python
- ✅ Fallback questions stay in TypeScript
- ✅ TypeScript has full control

**Cons:**
- ❌ Retries entire HTTP call (slower)
- ❌ Network overhead on each retry
- ❌ Python service doesn't know about retries
- ❌ Less efficient (HTTP overhead on retries)

---

### Option B: Retry in Python (API Level) ⭐ **RECOMMENDED**

**Architecture:**
```
TypeScript (generateQuestions)
  └─ Single HTTP call → Python service
      └─ Python: generate_questions_with_retry()
          ├─ Attempt 1: callOpenAI() + validation
          │   └─ Fails → Python retries
          ├─ Attempt 2: callOpenAI() + validation
          │   └─ Fails → Python retries
          └─ Attempt 3: callOpenAI() + validation
              └─ Success → Return questions
              └─ Or: All failed → Return error
```

**TypeScript:**
```typescript
export async function generateQuestions(...) {
  try {
    // Single HTTP call - Python handles retries
    const response = await fetch('http://localhost:8000/api/generate-questions', {
      method: 'POST',
      body: JSON.stringify({ userQuery, numQuestions, numAnswers })
    });
    
    if (!response.ok) {
      // Python failed after all retries
      return STATIC_FALLBACK;
    }
    
    const data = await response.json();
    return data.questions;
  } catch (error) {
    // Network error or Python service down
    return STATIC_FALLBACK;
  }
}
```

**Python:**
```python
MAX_RETRIES = 4

def generate_questions_with_retry(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> list[Question]:
    """Generate questions with retry logic"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            questions = call_openai_with_validation(
                user_query, num_questions, num_answers
            )
            return questions
        except Exception as e:
            print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            
            if attempt == MAX_RETRIES:
                raise  # Re-raise to caller
            
            # Exponential backoff
            time.sleep(2 ** (attempt - 1))
    
    raise Exception("All retries exhausted")

@app.post("/api/generate-questions")
async def generate_questions_endpoint(request: GenerateQuestionsRequest):
    try:
        questions = generate_questions_with_retry(
            request.userQuery,
            request.numQuestions,
            request.numAnswers
        )
        return {"success": True, "questions": [q.model_dump() for q in questions]}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pros:**
- ✅ Retries happen at API level (faster)
- ✅ No HTTP overhead on retries
- ✅ Python handles all OpenAI interaction
- ✅ Cleaner separation: Python = API + retry, TypeScript = orchestration
- ✅ More efficient (retries OpenAI directly, not HTTP)

**Cons:**
- ⚠️ Python needs retry logic code
- ⚠️ TypeScript loses some control
- ⚠️ Fallback still in TypeScript (but that's fine)

---

## 🎯 Recommendation: **Option B (Retry in Python)**

### Why Retry in Python is Better:

1. **Efficiency**
   - Retries OpenAI API directly (fast)
   - No HTTP overhead on retries
   - Only one HTTP call from TypeScript

2. **Separation of Concerns**
   - Python: All OpenAI interaction (API call + validation + retry)
   - TypeScript: Orchestration + fallback
   - Clear boundaries

3. **Better Error Handling**
   - Python can distinguish between:
     - OpenAI API errors (retry)
     - Validation errors (don't retry)
     - Network errors (retry)
   - TypeScript just handles: success or fallback

4. **Future-Proof**
   - When we add E2B, retry logic is already in Python
   - Consistent pattern for all Python services

---

## 🏗️ Implementation

### Python Service:

**File: `python-service/services/question_generator.py`**
```python
import os
import json
import time
from openai import OpenAI
from models.question import QuestionsResponse, Question

MAX_RETRIES = 4

def call_openai_with_validation(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> list[Question]:
    """Call OpenAI API and validate with Pydantic"""
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""..."""
    
    response = openai.chat.completions.create(...)
    content = response.choices[0].message.content
    
    if not content:
        raise ValueError("Empty response from OpenAI")
    
    parsed = json.loads(content)
    validated = QuestionsResponse(**parsed)
    
    return validated.questions

def generate_questions_with_retry(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> list[Question]:
    """Generate questions with retry logic and validation"""
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            questions = call_openai_with_validation(
                user_query, num_questions, num_answers
            )
            return questions
        except ValueError as e:
            # Validation error - don't retry
            raise e
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            
            if attempt < MAX_RETRIES:
                # Exponential backoff
                wait_time = 2 ** (attempt - 1)
                time.sleep(wait_time)
    
    # All retries failed
    raise Exception(f"All {MAX_RETRIES} attempts failed. Last error: {last_error}")
```

**File: `python-service/main.py`**
```python
from fastapi import FastAPI, HTTPException
from services.question_generator import generate_questions_with_retry

app = FastAPI()

@app.post("/api/generate-questions")
async def generate_questions_endpoint(request: GenerateQuestionsRequest):
    try:
        questions = generate_questions_with_retry(
            request.userQuery,
            request.numQuestions,
            request.numAnswers
        )
        return {
            "success": True,
            "questions": [q.model_dump() for q in questions]
        }
    except ValueError as e:
        # Validation error - bad request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # All retries failed
        return {
            "success": False,
            "error": str(e)
        }
```

### TypeScript Changes:

**File: `src/services/questionGenerator.ts`**
```typescript
// Simplified - no retry logic here
export async function generateQuestions(
  userQuery: string,
  numQuestions: number = 3,
  numAnswers: number = 3
): Promise<Question[]> {
  try {
    // Single HTTP call - Python handles retries
    const response = await fetch('http://localhost:8000/api/generate-questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userQuery, numQuestions, numAnswers })
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.questions;
    } else {
      // Python failed after all retries
      console.warn('Python service failed, using fallback');
      return STATIC_FALLBACK.slice(0, numQuestions);
    }
  } catch (error) {
    // Network error or Python service down
    console.error('Error calling Python service:', error);
    return STATIC_FALLBACK.slice(0, numQuestions);
  }
}
```

---

## 📊 Comparison

| Aspect | Retry in TypeScript | Retry in Python ⭐ |
|--------|---------------------|-------------------|
| **Efficiency** | Slower (HTTP retries) | Faster (API retries) |
| **HTTP Calls** | 1-4 calls | 1 call |
| **Separation** | Mixed | Clean |
| **Error Handling** | Basic | Better |
| **Code Location** | TypeScript | Python |
| **Fallback** | TypeScript | TypeScript |

---

## ✅ Final Recommendation

**Put retry logic in Python:**

**Why:**
1. ✅ More efficient (retries API directly)
2. ✅ Cleaner separation (Python = all OpenAI interaction)
3. ✅ Better error handling (can distinguish error types)
4. ✅ Only one HTTP call from TypeScript
5. ✅ Future-proof for E2B integration

**What lives where:**

**Python:**
- ✅ OpenAI API calls
- ✅ Pydantic validation
- ✅ Retry logic with exponential backoff
- ✅ Error handling and classification

**TypeScript:**
- ✅ HTTP call to Python service
- ✅ Fallback to static questions
- ✅ Session management
- ✅ Widget generation
- ✅ REST API endpoints

**Result:**
- Python: ~120 lines (API + validation + retry)
- TypeScript: ~30 lines (HTTP call + fallback)
- Clean separation
- Efficient retries
- Better architecture

---

## 💡 Alternative: Hybrid Approach

If you want TypeScript to have some control:

**Python:** Retries API calls (fast)
**TypeScript:** Retries HTTP calls if Python service is down (resilience)

But this is probably overkill - Python retry is sufficient.

---

## 🎯 Conclusion

**Retry logic should live in Python** because:
- It's more efficient
- Better separation of concerns
- Python handles all OpenAI interaction
- TypeScript just orchestrates and handles fallback

This gives you the best of both worlds: efficient retries in Python, simple orchestration in TypeScript.





