import requests
import json
import streamlit as st
import time
import re

class AIParser:
    """Handles AI API integration for intelligent resume parsing using OpenRouter"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        model_name: str = "deepseek/deepseek-chat-v3-0324"
    ):
        if not api_key:
            raise ValueError("API key is required for AIParser initialization.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Resume Parser"
        }

    def parse_resume(self, resume_text: str):
        """Main parsing function focused on extracting key information"""
        try:
            if not resume_text or not resume_text.strip():
                return self._create_empty_structure()

            prompt = self._create_parsing_prompt(resume_text)
            response = self._make_api_call_with_retry(prompt)

            if response:
                return self._parse_api_response(response)
            else:
                return self._create_empty_structure()

        except Exception as e:
            st.error(f"Error parsing resume with AI: {str(e)}")
            return self._create_empty_structure()

    def _create_parsing_prompt(self, resume_text: str):
        """Create focused prompt for extracting specific information"""
        max_chars = 12000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "..."

        return f"""
You are an expert resume parser. Extract ONLY the following specific information from this resume text:

Resume Text:
{resume_text}

Extract and return ONLY a valid JSON object with this EXACT structure:
{{
    "first_name": "candidate's first name only",
    "family_name": "candidate's last/family name only", 
    "email": "email address",
    "phone": "phone number",
    "job_title": "current or most recent job title/position"
}}

IMPORTANT RULES:
1. Return ONLY valid JSON, no extra text
2. Use empty string "" for missing values
3. For first_name and family_name: split the full name properly
4. For job_title: extract the most recent or current position title
5. Extract complete phone number with area code if available
6. Ensure email is valid format

Focus on accuracy over completeness.
"""

    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3):
        """Retry wrapper for API call"""
        for attempt in range(max_retries):
            try:
                return self._make_api_call(prompt)
            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"AI API failed after {max_retries} attempts: {str(e)}")
                    return None
                else:
                    st.warning(f"AI API attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(1.5 * (attempt + 1))
        return None

    def _make_api_call(self, prompt: str):
        """Make API request to OpenRouter"""
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.1
        }

        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")

    def _parse_api_response(self, response_text: str):
        """Extract and validate JSON from AI response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                parsed_data = json.loads(json_text)
            else:
                parsed_data = json.loads(response_text)

            return self._validate_parsed_data(parsed_data)

        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse AI response as JSON: {str(e)}")
            st.code(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            return self._create_empty_structure()

    def _validate_parsed_data(self, data: dict):
        """Validate and clean parsed data"""
        validated_data = {
            "first_name": str(data.get("first_name", "")).strip(),
            "family_name": str(data.get("family_name", "")).strip(),
            "email": str(data.get("email", "")).strip(),
            "phone": str(data.get("phone", "")).strip(),
            "job_title": str(data.get("job_title", "")).strip()
        }

        # Clean email format
        email = validated_data["email"]
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            validated_data["email"] = ""

        # Clean phone number
        phone = validated_data["phone"]
        if phone:
            # Remove non-digit characters except +, -, (, ), space
            cleaned_phone = re.sub(r'[^\d\-\(\)\.\+\s]', '', phone)
            validated_data["phone"] = cleaned_phone.strip()

        return validated_data

    def _create_empty_structure(self):
        """Return empty structure when parsing fails"""
        return {
            "first_name": "",
            "family_name": "",
            "email": "",
            "phone": "",
            "job_title": ""
        }
