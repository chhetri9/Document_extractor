import json
import os

from utils import create_field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def extract_invoice_data(document_text):

    prompt = f"""
    Extract the following invoice information from the text below.

    Return ONLY valid JSON.

    Use EXACTLY these keys:
    - invoice_number
    - customer_name
    - amount
    - date

    Rules:
    - Keys MUST be lowercase
    - If a field is missing, return null
    - Do NOT hallucinate values
    - Return only valid JSON

    Invoice Text:
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

        # Remove markdown formatting if present
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

            "document_type": "invoice",

            "fields": {

                "invoice_number": create_field(
                    value=parsed_data.get("invoice_number"),
                    confidence="high" if parsed_data.get("invoice_number") else "low",
                    note=None if parsed_data.get("invoice_number") else "Invoice number not found"
                ),

                "customer_name": create_field(
                    value=parsed_data.get("customer_name"),
                    confidence="medium" if parsed_data.get("customer_name") else "low",
                    note=None if parsed_data.get("customer_name") else "Customer name not found"
                ),

                "amount": create_field(
                    value=parsed_data.get("amount"),
                    confidence="high" if parsed_data.get("amount") else "low",
                    note=None if parsed_data.get("amount") else "Amount not found"
                ),

                "date": create_field(
                    value=parsed_data.get("date"),
                    confidence="medium" if parsed_data.get("date") else "low",
                    note=None if parsed_data.get("date") else "Date not found"
                )
            }
        }

        return structured_data

    except json.JSONDecodeError:

        return {
            "error": "JSON parsing failed",
            "raw_output": output
        }