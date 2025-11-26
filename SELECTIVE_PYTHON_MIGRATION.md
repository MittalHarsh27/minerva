# Selective Python Migration - API Calling Logic Only

## 🎯 Strategy: Minimal Migration

**Goal:** Migrate ONLY the OpenAI API calling logic to Python, keep everything else in TypeScript.

---

## 📊 Current Code Analysis

### What We Have Now:

**`src/services/questionGenerator.ts`:**
```typescript
1. generateQuestions() - Orchestration + retry logic
2. callOpenAI() - Pure OpenAI API call + parsing
3. Validation with Zod
4. Static fallback questions
```

**Lines breakdown:**
- Lines 24-47: `generateQuestions()` - Orchestration (retry, fallback)
- Lines 49-110: `callOpenAI()` - **API CALLING LOGIC** ← Migrate this
- Lines 6-22: Static fallback - Keep in TypeScript

---

## ✅ What to Migrate (Minimal)

### **ONLY: `callOpenAI()` function**

**Current (TypeScript):**
```typescript
async function callOpenAI(
  userQuery: string,
  numQuestions: number,
  numAnswers: number
): Promise<Question[]> {
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  
  const prompt = `...`;
  
  const response = await openai.chat.completions.create({...});
  
  const parsed = JSON.parse(content);
  return parsed.questions;
}
```

**Python Equivalent:**
```python
# python-service/services/openai_client.py
def call_openai(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> list[dict]:
    from openai import OpenAI
    
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"..."
    
    response = openai.chat.completions.create(...)
    
    parsed = json.loads(response.choices[0].message.content)
    return parsed["questions"]
```

**What this includes:**
- ✅ OpenAI client initialization
- ✅ Prompt construction
- ✅ API call to OpenAI
- ✅ Response parsing
- ✅ Basic error handling

**What this excludes:**
- ❌ Retry logic (stays in TypeScript)
- ❌ Validation (stays in TypeScript with Zod)
- ❌ Fallback questions (stays in TypeScript)
- ❌ Session management (stays in TypeScript)

---

## 🏗️ Architecture

### Before (All TypeScript):
```
┌─────────────────────┐
│  Express Server     │
│  (TypeScript)       │
│                     │
│  generateQuestions()│
│    ├─ callOpenAI()  │ ← OpenAI API call
│    ├─ Validation    │
│    └─ Retry logic    │
└─────────────────────┘
```

### After (Selective Migration):
```
┌─────────────────────┐
│  Express Server     │
│  (TypeScript)       │
│                     │
│  generateQuestions()│
│    ├─ HTTP call ────┼──→ ┌──────────────────┐
│    ├─ Validation    │    │ Python Service   │
│    └─ Retry logic    │    │ (FastAPI)        │
└─────────────────────┘    │                  │
                            │ call_openai()    │ ← OpenAI API call
                            │ (Pure API logic) │
                            └──────────────────┘
```

---

## 📝 Implementation Plan

### Python Service (Minimal):

**File: `python-service/services/openai_client.py`**
```python
import os
import json
from openai import OpenAI

def call_openai_api(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> list[dict]:
    """Pure OpenAI API call - no validation, no retry"""
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""Given this user request: "{user_query}"
    
Generate {num_questions} multiple choice questions...
"""
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You generate survey questions. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=500
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenAI")
    
    parsed = json.loads(content)
    if "questions" not in parsed or not isinstance(parsed["questions"], list):
        raise ValueError("Invalid response structure")
    
    return parsed["questions"]
```

**File: `python-service/main.py`**
```python
from fastapi import FastAPI
from services.openai_client import call_openai_api

app = FastAPI()

@app.post("/api/call-openai")
async def call_openai_endpoint(request: dict):
    """Minimal endpoint - just calls OpenAI API"""
    try:
        questions = call_openai_api(
            request["userQuery"],
            request["numQuestions"],
            request["numAnswers"]
        )
        return {"success": True, "questions": questions}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### TypeScript Changes (Minimal):

**File: `src/services/questionGenerator.ts`**
```typescript
// Keep everything EXCEPT callOpenAI()

async function callOpenAI(
  userQuery: string,
  numQuestions: number,
  numAnswers: number
): Promise<Question[]> {
  // REPLACE with HTTP call to Python service
  const response = await fetch('http://localhost:8000/api/call-openai', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userQuery, numQuestions, numAnswers })
  });
  
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error);
  }
  
  return data.questions;
}

// Keep generateQuestions() exactly as-is
// Keep validation with Zod
// Keep retry logic
// Keep static fallback
```

---

## ✅ Benefits of Selective Migration

1. **Minimal Changes:** Only ~60 lines of code change
2. **Low Risk:** Most logic stays in TypeScript
3. **Easy Rollback:** Can revert quickly if needed
4. **Isolated API Calls:** Python handles only OpenAI interaction
5. **Future-Proof:** Sets pattern for more Python services later
6. **Better Error Handling:** Python can handle OpenAI-specific errors better

---

## ⚠️ Tradeoffs

### Pros:
- ✅ Minimal migration effort
- ✅ Keeps TypeScript validation and retry logic
- ✅ Python only for what it's best at (API calls)
- ✅ Easy to test independently

### Cons:
- ⚠️ Adds HTTP overhead (~10-50ms)
- ⚠️ Need to run two services
- ⚠️ More complex deployment

---

## 🎯 Recommended Approach

### Option A: Pure API Call Only (Recommended)
**Migrate:** Only `callOpenAI()` function
**Keep in TypeScript:**
- Retry logic
- Validation (Zod)
- Fallback questions
- Session management

**Python Service:**
- Single endpoint: `POST /api/call-openai`
- Pure OpenAI API call
- Returns raw questions array
- No validation, no retry

**Benefits:**
- Minimal changes
- TypeScript keeps control flow
- Python only for API interaction

---

### Option B: API Call + Validation
**Migrate:** `callOpenAI()` + Validation
**Keep in TypeScript:**
- Retry logic
- Fallback questions
- Session management

**Python Service:**
- Endpoint with Pydantic validation
- Returns validated questions
- Better validation than Zod

**Benefits:**
- Better validation (Pydantic)
- Still minimal migration
- TypeScript keeps orchestration

---

## 📋 Migration Steps (Selective)

1. **Create minimal Python service** (50 lines)
   - FastAPI app
   - Single endpoint: `/api/call-openai`
   - Pure OpenAI API call

2. **Update TypeScript** (10 lines changed)
   - Replace `callOpenAI()` implementation
   - Keep everything else the same

3. **Test independently**
   - Test Python service alone
   - Test TypeScript with Python service

4. **Deploy together**
   - Run both services
   - TypeScript calls Python via HTTP

---

## 🎯 Recommendation

**Go with Option A (Pure API Call Only):**

**Why:**
- Smallest possible migration
- Lowest risk
- Python only for what it's best at
- Easy to extend later

**What gets migrated:**
- ~60 lines: OpenAI API calling logic

**What stays in TypeScript:**
- ~50 lines: Retry logic, validation, fallback
- All session management
- All widget generation
- All REST API endpoints

**Result:**
- Clean separation: Python = API calls, TypeScript = everything else
- Easy to maintain
- Easy to test
- Easy to extend

---

## 💡 Alternative: Even More Selective

If you want to be even more minimal, you could:

**Option C: Just the OpenAI SDK call**
- Python service only wraps `openai.chat.completions.create()`
- TypeScript does prompt construction
- TypeScript does all parsing
- Python is just a thin wrapper

**But this might be too minimal** - the prompt construction and parsing are part of the "API calling logic" that benefits from Python.

---

## ✅ Final Recommendation

**Migrate:**
- ✅ `callOpenAI()` function (lines 49-110)
- ✅ Prompt construction
- ✅ OpenAI API call
- ✅ Response parsing

**Keep in TypeScript:**
- ✅ `generateQuestions()` orchestration
- ✅ Retry logic
- ✅ Zod validation
- ✅ Static fallback
- ✅ Everything else

**Python Service:**
- Single endpoint: `POST /api/call-openai`
- ~50 lines of code
- Pure API interaction

This gives you the benefits of Python for API calls while keeping everything else in TypeScript where it works well.





