# src/

TypeScript source code for the Express.js server.

## Structure

### `server.ts`
Main Express server entry point. Handles:
- HTTP endpoints (`/api/questions`, `/submit-answers`, `/api/widget/:sessionId`)
- Static file serving from `public/`
- Authentication middleware integration
- Session management
- Search history saving
- User profile fetching for personalization

### `middleware/`

#### `auth.ts`
Authentication middleware:
- `requireAuth` - Express middleware that validates JWT tokens from Supabase
- `getUserId` - Extracts user ID from authenticated requests
- Uses Supabase service role key to verify tokens

### `services/`

#### `questionGenerator.ts`
Calls Python service at `http://localhost:8000/api/generate-questions` to generate questions based on user queries.

#### `sessionService.ts`
Manages Q&A sessions in Supabase:
- `createSession()` - Creates new session with questions
- `getSession()` - Retrieves session by ID
- `updateSessionAnswers()` - Updates session with user answers
- Sessions expire after 24 hours

#### `userProfileService.ts`
Fetches user profiles from Supabase `user_profiles` table:
- `getUserProfile()` - Gets user demographics (age, gender, location) for personalization

#### `searchHistoryService.ts`
Manages search history in Supabase `user_search_history` table:
- `saveSearchHistory()` - Saves search queries and results
- `getSearchHistory()` - Retrieves last 10 searches per user
- Automatic cleanup keeps only last 10 entries per user

### `types/`

#### `question.types.ts`
TypeScript types and Zod schemas for questions:
- `Question` - Question object with id, text, and answers array
- `QuestionsResponse` - Response containing array of questions

#### `express.d.ts`
Type augmentation for Express Request to include `user` property with authenticated user info.

