# Q&A Recommendation Web App

A standalone web application that provides personalized recommendations through interactive question-and-answer sessions. Users can ask for recommendations, answer dynamically generated questions, and receive personalized suggestions.

## Overview

This web app helps users get personalized recommendations by asking them a series of questions. For example, when a user asks "Recommend me chinos for work", the app will:

1. Generate personalized questions based on the query (e.g., "What's your preferred fit?")
2. Present an interactive Q&A widget with clickable answer options
3. Collect the user's selections
4. Process answers and provide personalized recommendations

## Features

- 🎯 **Dynamic Question Generation**: Uses OpenAI to generate context-aware questions based on user queries
- ⚙️ **Configurable**: Easily adjust the number of questions (n) and answers (m) per question
- 📝 **Session Management**: Tracks user answers across multiple questions
- 🎨 **Modern UI**: Beautiful chat interface with gradient design and smooth animations
- 🔄 **RESTful API**: Clean REST API endpoints for easy integration
- 🌐 **Standalone Web App**: No external dependencies, runs independently

## Configuration

The app uses environment variables for configuration:

- `NUM_QUESTIONS`: Number of questions to ask (default: 3)
- `NUM_ANSWERS`: Number of answer options per question (default: 4)
- `PORT`: Server port (default: 3001)
- `OPENAI_API_KEY`: Your OpenAI API key (required for question generation)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd chatgpt-qa-agent
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PORT=3001
   NUM_QUESTIONS=3
   NUM_ANSWERS=3
   ```

4. **Build the TypeScript code:**
   ```bash
   npm run build
   ```

5. **Start the server:**
   ```bash
   npm start
   ```

   Or for development with auto-rebuild:
   ```bash
   npm run dev
   ```

## Usage

### 1. Start the Server

```bash
npm start
```

The server will start on `http://localhost:3001` (or your configured PORT).

### 2. Open the Web App

Open your browser and navigate to:
```
http://localhost:3001
```

### 3. Use the App

1. Type a recommendation request in the chat input (e.g., "I want shoes for work")
2. The app will generate personalized questions based on your query
3. Click on your preferred answers for each question
4. Click "Submit Answers" when all questions are answered
5. Your answers will be processed and stored

## Project Structure

```
chatgpt-qa-agent/
├── src/
│   ├── server.ts              # Main server with REST API endpoints
│   ├── services/
│   │   └── questionGenerator.ts  # Dynamic question generation logic
│   └── types/
│       └── question.types.ts     # TypeScript type definitions
├── public/
│   └── index.html             # Frontend web interface
├── docs/
│   └── e2b/                   # E2B integration docs (for future use)
├── dist/                      # Compiled JavaScript (generated)
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript configuration
├── .env                       # Environment variables (create this)
└── README.md                  # This file
```

## How It Works

### 1. Question Generation
When a user submits a query:
- The frontend sends a `POST /api/questions` request with the query
- The server uses OpenAI to generate context-aware questions
- Questions are validated using Zod schemas
- A session is created and questions are returned

### 2. Widget Display
- The frontend fetches the widget HTML via `GET /api/widget/:sessionId`
- The widget displays questions with clickable answer buttons
- Users can select answers with visual feedback

### 3. Answer Submission
- When all questions are answered, users click "Submit Answers"
- Answers are sent to `POST /submit-answers` endpoint
- Answers are stored in the session

### 4. Answer Processing
- The `POST /api/answers` endpoint processes submitted answers
- Generates a recommendation summary
- Returns personalized recommendations based on user preferences

## API Endpoints

### POST `/api/questions`
Generates questions based on a user query.

**Request:**
```json
{
  "query": "I want shoes for work"
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "session_1234567890_abc123",
  "questions": [
    {
      "id": "q1",
      "text": "What color of shoes do you prefer for work?",
      "answers": ["Black", "Brown", "Navy"]
    }
  ]
}
```

### GET `/api/widget/:sessionId`
Returns the widget HTML for a given session.

**Response:** HTML content (text/html)

### POST `/api/answers`
Processes user answers and generates recommendations.

**Request:**
```json
{
  "sessionId": "session_1234567890_abc123",
  "answers": {
    "What color of shoes do you prefer for work?": "Black",
    "Which style do you prefer?": "Oxfords"
  }
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "session_1234567890_abc123",
  "originalQuery": "I want shoes for work",
  "answers": { ... },
  "summary": "- **What color...**: Black\n- **Which style...**: Oxfords",
  "message": "Based on your preferences..."
}
```

### POST `/submit-answers`
Alternative endpoint for submitting answers (used by widget).

**Request:**
```json
{
  "sessionId": "session_1234567890_abc123",
  "answers": { ... }
}
```

### GET `/health`
Health check endpoint. Returns server status.

## Customization

### Adjusting Configuration

Set environment variables before starting:

```bash
NUM_QUESTIONS=5 NUM_ANSWERS=3 PORT=4000 npm start
```

### Styling the UI

Modify the CSS in the `generateQAWidget()` function in `src/server.ts` or update the styles in `public/index.html`.

### Question Generation

The question generation logic is in `src/services/questionGenerator.ts`. You can customize:
- The OpenAI model used
- The prompt structure
- Retry logic and fallback questions

## Development

### Build
```bash
npm run build
```

### Run in Development Mode
```bash
npm run dev
```

### Check Health
```bash
curl http://localhost:3001/health
```

## Troubleshooting

### Server won't start
- Check if port 3001 is already in use
- Try a different port: `PORT=3002 npm start`
- Verify your `.env` file exists and contains `OPENAI_API_KEY`

### Questions not generating
- Verify your `OPENAI_API_KEY` is set correctly in `.env`
- Check server logs for OpenAI API errors
- Ensure you have sufficient OpenAI API credits

### Widget not displaying
- Check browser console for errors
- Verify the session ID is valid
- Ensure the server is running and accessible

## Future Enhancements

### E2B Integration
E2B integration documentation is available in `docs/e2b/` for future implementation. This will enable:
- Advanced code execution capabilities
- Web search integration (Exa, Perplexity)
- Enhanced recommendation generation

### Planned Features
1. **Database Integration**: Connect to a real product/service database
2. **Persistent Storage**: Use Redis or a database for session management
3. **Advanced Recommendations**: Implement ML-based recommendation algorithms
4. **User Authentication**: Add user accounts and preferences
5. **Analytics**: Track user interactions and improve recommendations
6. **Testing**: Add comprehensive unit and integration tests

## License

MIT

## Contributing

Feel free to submit issues and enhancement requests!
