import requests
import json
import streamlit as st
import time
import sys
import platform
import re


class AIParser:
    """Handles AI API integration for intelligent resume parsing, supporting OpenRouter."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        model_name: str = "deepseek/deepseek-chat-v3-0324"
    ):
        if not api_key:
            raise ValueError("API key is required for AIParser initialization.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # ensure no trailing slash
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Change this if OpenRouter rejects localhost
            "HTTP-Referer": "http://localhost",
            "X-Title": "Resume Parser"
        }

        # Debug environment info
        st.write(f"DEBUG: Initializing AIParser with base_url: {self.base_url}, model: {self.model_name}")
        st.write(f"DEBUG: requests library version: {requests.__version__}")
        st.write(f"DEBUG: Python version: {sys.version}")
        st.write(f"DEBUG: Platform: {platform.platform()}")

    def test_connection(self):
        """Optional API test. Call this manually if you want to verify connectivity."""
        try:
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 1,
                "temperature": 0
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=test_payload,
                timeout=10
            )

            if response.status_code != 200:
                raise Exception(f"API test failed: {response.status_code} - {response.text}")
            st.success("API connection successful ✅")

        except Exception as e:
            st.error(f"API connection test failed: {str(e)}")
            raise

    def parse_resume(self, resume_text: str):
        """Main parsing function."""
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
        """Prepare prompt for LLM."""
        max_chars = 15000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "..."

        return f"""
You are an expert resume parser. Analyze the following resume text and extract structured information in JSON format.

Resume Text:
{resume_text}

Please extract and return ONLY a valid JSON object with the following structure:
{{
    "name": "candidate full name",
    "email": "email address",
    "phone": "phone number",
    "skills": ["skill1", "skill2", "skill3"],
    "experience": [
        {{
            "company": "company name",
            "position": "job title",
            "duration": "employment period",
            "description": "brief job description"
        }}
    ],
    "education": [
        {{
            "institution": "school/university name",
            "degree": "degree type",
            "field": "field of study",
            "year": "graduation year"
        }}
    ],
    "summary": "professional summary or objective"
}}

Rules:
1. Return ONLY valid JSON, no extra text
2. Use "" or [] for missing values
3. Extract all skills, technical + soft
4. Include all experience & education entries
"""

    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3):
        """Retry wrapper for API call."""
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
        """Actual API request."""
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
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
        """Extract and validate JSON from LLM response."""
        try:
            # Extract JSON with regex to avoid slicing errors
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                parsed_data = json.loads(json_text)
            else:
                parsed_data = json.loads(response_text)

            return self._validate_parsed_data(parsed_data)

        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse AI response as JSON: {str(e)}")
            st.code(response_text)
            return self._create_empty_structure()

    def _validate_parsed_data(self, data: dict):
        """Ensure parsed data matches expected structure."""
        validated_data = {
            "name": str(data.get("name", "")).strip(),
            "email": str(data.get("email", "")).strip(),
            "phone": str(data.get("phone", "")).strip(),
            "skills": [],
            "experience": [],
            "education": [],
            "summary": str(data.get("summary", "")).strip()
        }

        if isinstance(data.get("skills"), list):
            validated_data["skills"] = [str(skill).strip() for skill in data["skills"] if str(skill).strip()]

        if isinstance(data.get("experience"), list):
            for exp in data["experience"]:
                if isinstance(exp, dict):
                    validated_exp = {
                        "company": str(exp.get("company", "")).strip(),
                        "position": str(exp.get("position", "")).strip(),
                        "duration": str(exp.get("duration", "")).strip(),
                        "description": str(exp.get("description", "")).strip()
                    }
                    if any(validated_exp.values()):
                        validated_data["experience"].append(validated_exp)

        if isinstance(data.get("education"), list):
            for edu in data["education"]:
                if isinstance(edu, dict):
                    validated_edu = {
                        "institution": str(edu.get("institution", "")).strip(),
                        "degree": str(edu.get("degree", "")).strip(),
                        "field": str(edu.get("field", "")).strip(),
                        "year": str(edu.get("year", "")).strip()
                    }
                    if any(validated_edu.values()):
                        validated_data["education"].append(validated_edu)

        return validated_data

    def _create_empty_structure(self):
        """Fallback empty structure."""
        return {
            "name": "",
            "email": "",
            "phone": "",
            "skills": [],
            "experience": [],
            "education": [],
            "summary": ""
        }
