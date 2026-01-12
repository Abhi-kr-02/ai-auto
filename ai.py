from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found. Please set it as an environment variable "
        "or create a .env file with OPENAI_API_KEY=your-key-here"
    )

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
You are an AI sales assistant.

Rules:
- Reply under 40 words
- Ask only ONE question
- No emojis
- Be polite
Return JSON only:
{ "reply": "...", "should_stop": false }
"""

def generate_ai_reply(context: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
        temperature=0.4
    )
    return json.loads(response.choices[0].message.content)
