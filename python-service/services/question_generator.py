"""
Question generator service with retry logic.
Handles OpenAI API calls, Pydantic validation, and retry with exponential backoff.
"""

import os
import json
import time
from typing import List
from openai import OpenAI
from pydantic import ValidationError

from models.question import Question, QuestionsResponse

MAX_RETRIES = 4


def call_openai_with_validation(
    user_query: str,
    num_questions: int,
    num_answers: int
) -> List[Question]:
    """
    Call OpenAI API and validate response with Pydantic.
    
    Args:
        user_query: User's recommendation request
        num_questions: Number of questions to generate
        num_answers: Number of answer options per question
    
    Returns:
        List of validated Question objects
    
    Raises:
        ValueError: For validation errors (don't retry)
        Exception: For API/network errors (retry)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    openai = OpenAI(api_key=api_key)
    
    prompt = f"""Given this user request: "{user_query}"

Generate {num_questions} multiple choice questions to understand their preferences.
Each question should have exactly {num_answers} answer options.

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "id": "q1",
      "text": "Question text?",
      "answers": ["Option 1", "Option 2", "Option 3"]
    }}
  ]
}}

Requirements:
- Clear, specific questions
- Exactly {num_answers} answers per question
- Concise answer options (2-4 words)
- Relevant to the user's request
- Use IDs: q1, q2, q3, etc."""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You generate survey questions. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")
        
        parsed = json.loads(content)
        
        if not parsed.get("questions") or not isinstance(parsed["questions"], list):
            raise ValueError("Invalid response structure: missing or invalid 'questions' array")
        
        # Validate with Pydantic
        validated = QuestionsResponse(**parsed)
        return validated.questions
        
    except ValidationError as e:
        # Validation errors - don't retry, raise immediately
        raise ValueError(f"Validation error: {e}")
    except json.JSONDecodeError as e:
        # JSON parsing errors - don't retry
        raise ValueError(f"Invalid JSON response: {e}")
    except Exception as e:
        # API/network errors - will be retried
        raise Exception(f"OpenAI API error: {e}")


def generate_questions_with_retry(
    user_query: str,
    num_questions: int = 3,
    num_answers: int = 3
) -> List[Question]:
    """
    Generate questions with retry logic and validation.
    
    Retries on API/network errors, but not on validation errors.
    Raises an exception if all retries fail.
    
    Args:
        user_query: User's recommendation request
        num_questions: Number of questions to generate (default: 3)
        num_answers: Number of answer options per question (default: 3)
    
    Returns:
        List of Question objects
    
    Raises:
        ValueError: For validation errors (immediate failure, no retry)
        Exception: For API/network errors after all retries exhausted
    """
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            questions = call_openai_with_validation(
                user_query, num_questions, num_answers
            )
            return questions
            
        except ValueError as e:
            # Validation error - don't retry, raise immediately
            print(f"Validation error (attempt {attempt}/{MAX_RETRIES}): {e}")
            raise ValueError(f"Question generation failed: {e}")
            
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            
            if attempt < MAX_RETRIES:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** (attempt - 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    # All retries failed - raise exception
    error_message = f"Question generation failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    print(error_message)
    raise Exception(error_message)

