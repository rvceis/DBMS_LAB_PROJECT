import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_AI_API"))


def get_response(message: str) -> str:
    """Try a list of models (newer first). If all fail, return a helpful error message.

    The user recently created an account; some models may be unavailable for the account
    (quota/plan). We try multiple models to increase the chance of success.
    """
    preferred_models = ["gpt-4o-mini", "gpt-3.5-turbo"]

    # Basic validation
    if not message or not message.strip():
        return "Please provide a message."

    # If no API key present, return a clear message
    if not os.getenv("OPEN_AI_API"):
        return "OpenAI API key is not configured. Please set OPEN_AI_API in your .env file."

    for model in preferred_models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful health assistant. Provide basic health guidance, diet tips, and mental health suggestions. Do not provide medical diagnosis. Always recommend consulting a doctor for serious symptoms."
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            # Extract reply safely
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            print(f"OpenAI error with model {model}: {err}")
            # Try next model if quota/rate-limit or other transient error
            # If it's a definitive configuration error, continue to next model anyway
            continue

    # If we reach here, all models failed
    return "Sorry — could not reach the OpenAI API. Please check your API key, billing/quotas, and try again later."