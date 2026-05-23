import os
import json

from utils import create_field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def extract_resume_data(document_text):

    prompt = f"""
    Extract the following information from this resume.

    Return ONLY valid JSON.

    Use EXACTLY these keys:
    - name
    - email
    - phone
    - skills

    Rules:
    - Keys MUST be lowercase
    - If a field is missing, return null
    - Do NOT hallucinate values
    - Return only valid JSON

    Resume Text:
    {document_text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    output = response.choices[0].message.content

    try:

        # Remove markdown if present
        cleaned_output = (
            output.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        # Parse JSON
        parsed_data = json.loads(cleaned_output)

        # Normalize keys
        parsed_data = {
            key.lower(): value
            for key, value in parsed_data.items()
        }

        # Create structured response
        structured_data = {

            "document_type": "resume",

            "fields": {

                "name": create_field(
                    value=parsed_data.get("name"),
                    confidence="high" if parsed_data.get("name") else "low",
                    note=None if parsed_data.get("name") else "Name not found"
                ),

                "email": create_field(
                    value=parsed_data.get("email"),
                    confidence="high" if parsed_data.get("email") else "low",
                    note=None if parsed_data.get("email") else "Email not found"
                ),

                "phone": create_field(
                    value=parsed_data.get("phone"),
                    confidence="medium" if parsed_data.get("phone") else "low",
                    note=None if parsed_data.get("phone") else "Phone number not found"
                ),

                "skills": create_field(
                    value=parsed_data.get("skills"),
                    confidence="medium" if parsed_data.get("skills") else "low",
                    note=None if parsed_data.get("skills") else "Skills not found"
                )
            }
        }

        return structured_data

    except json.JSONDecodeError:

        return {
            "error": "JSON parsing failed",
            "raw_output": output
        }