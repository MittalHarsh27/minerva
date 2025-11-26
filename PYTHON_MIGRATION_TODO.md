# Python Migration TODO - Current Codebase

## 📋 What Can Be Migrated NOW (Not Future Features)

### ✅ **1. Question Generation Service** 
**Current File:** `src/services/questionGenerator.ts` (112 lines)

**What it does:**
- Calls OpenAI API to generate questions
- Validates response with Zod
- Retry logic with exponential backoff
- Fallback to static questions

**Python Equivalent:**
- `python-service/services/question_generator.py`
- Uses Pydantic for validation (better than Zod)
- Same retry logic
- Same fallback mechanism

**Lines of code:** ~112 lines → ~80 lines (cleaner in Python)

---

### ✅ **2. Question Type Definitions**
**Current File:** `src/types/question.types.ts` (16 lines)

**What it does:**
- Zod schemas for Question and QuestionsResponse
- TypeScript type inference

**Python Equivalent:**
- `python-service/models/question.py`
- Pydantic models (more powerful than Zod)
- Better validation rules
- Automatic JSON serialization

**Lines of code:** ~16 lines → ~20 lines (but more powerful)

---

### ✅ **3. Question Generation Call in Server**
**Current File:** `src/server.ts` (line 55)

**What it does:**
- Calls `generateQuestions()` function
- Direct function call

**Python Equivalent:**
- HTTP call to Python FastAPI service
- `fetch('http://localhost:8000/api/generate-questions')`

**Change:** 1 line → 5-10 lines (HTTP call instead of function call)

---

## ❌ **What Should STAY in TypeScript**

### 1. Express Server (`src/server.ts`)
- REST API endpoints
- Session management
- Widget HTML generation
- Static file serving

**Why:** Node.js is excellent for web servers, no need to change

### 2. Frontend (`public/index.html`)
- Chat interface
- Widget rendering
- Answer submission

**Why:** Frontend stays as-is

---

## 📊 Migration Summary

**Files to Create:**
- `python-service/main.py` - FastAPI app
- `python-service/services/question_generator.py` - Question generation logic
- `python-service/models/question.py` - Pydantic models
- `python-service/requirements.txt` - Python dependencies
- `python-service/.env` - Environment variables (or use existing)

**Files to Modify:**
- `src/server.ts` - Replace `generateQuestions()` call with HTTP call

**Files to Delete (after migration):**
- `src/services/questionGenerator.ts` - Replaced by Python service
- `src/types/question.types.ts` - Replaced by Pydantic models (or keep for TypeScript types)

**Lines of Code:**
- TypeScript: ~128 lines to migrate
- Python: ~100 lines to create
- Net: Cleaner, more maintainable code

---

## 🎯 Benefits

1. **Better Validation:** Pydantic > Zod
2. **Cleaner Code:** Python is more readable for this logic
3. **Easier Testing:** Python testing is simpler
4. **Future-Proof:** Sets up pattern for E2B integration
5. **Independent Scaling:** Python service can scale separately

---

## ⚠️ Considerations

1. **Service Communication:** Need HTTP between Node.js and Python
2. **Error Handling:** Handle Python service being down
3. **Deployment:** Need to deploy both services
4. **Development:** Need to run both services locally

---

## 🚀 Quick Start

After migration, you'll have:
```
Node.js (Port 3001)          Python (Port 8000)
├── Express Server      ───→  ├── FastAPI Service
├── REST APIs                 ├── Question Generator
├── Session Management        ├── Pydantic Models
└── Widget Generation         └── OpenAI Integration
```

**Start commands:**
```bash
# Terminal 1: Node.js server
npm start

# Terminal 2: Python service
cd python-service
uvicorn main:app --port 8000
```

---

## ✅ TODO List Created

See the TODO list with 12 tasks for step-by-step migration.





