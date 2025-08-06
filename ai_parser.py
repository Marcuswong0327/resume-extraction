import requests
import json
import streamlit as st
import time
import sys
import platform
import certifi

class AIParser:
    """Handles AI API integration for intelligent resume parsing, supporting OpenRouter."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1/chat/completions", model_name: str = "deepseek/deepseek-chat-v3-0324"):
        if not api_key:
            raise ValueError("API key is required for AIParser initialization.")

        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Resume Parser"
        }

        try:
            self.ca_bundle_path = certifi.where()
            st.write(f"DEBUG: certifi CA bundle path: {self.ca_bundle_path}")
        except Exception as e:
            st.warning(f"WARNING: Could not determine certifi CA bundle path: {e}. HTTPS verification might fail.")
            self.ca_bundle_path = None

        st.write(f"DEBUG: Initializing AIParser with base_url: {self.base_url}, model: {self.model_name}")
        try:
            st.write(f"DEBUG: requests library version: {requests.__version__}")
            st.write(f"DEBUG: Python version: {sys.version}")
            st.write(f"DEBUG: Platform: {platform.platform()}")
        except AttributeError:
            st.write("DEBUG: Could not get requests version or system info.")

        self._test_connection()
https://github.com/Marcuswong0327/resume-extraction/tree/main
    def _test_connection(self):
        try:
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=test_payload,
                timeout=10,
                verify=self.ca_bundle_path if self.ca_bundle_path else True
            )

            if response.status_code != 200:
                raise Exception(f"API test failed: {response.status_code} - {response.text}")

        except Exception as e:
            raise Exception(f"API connection test failed: {str(e)}")

    def parse_resume(self, resume_text: str):
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
        max_chars = 15000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "..."

        prompt = f"""
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
1. Return ONLY valid JSON, no additional text or explanations
2. If information is not found, use empty string "" or empty array []
3. Extract all skills mentioned throughout the resume
4. Include all work experience entries with as much detail as possible
5. Include all education entries found
6. Be thorough and accurate in extraction
7. For skills, include both technical and soft skills
8. For experience, capture company names, positions, and durations accurately
"""
        return prompt

    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                response = self._make_api_call(prompt)
                if response:
                    return response

            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"AI API failed after {max_retries} attempts: {str(e)}")
                    return None
                else:
                    st.warning(f"AI API attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)

        return None

    def _make_api_call(self, prompt: str):
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 3000,
                "temperature": 0.1,
                "stream": False
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60,
                verify=self.ca_bundle_path if self.ca_bundle_path else True
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                error_msg = f"AI API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)

        except requests.exceptions.Timeout:
            raise Exception("AI API request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error calling AI API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling AI API: {str(e)}")

    def _parse_api_response(self, response_text: str):
        try:
            response_text = response_text.strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]

            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx + 1]
                parsed_data = json.loads(json_text)
            else:
                parsed_data = json.loads(response_text)

            return self._validate_parsed_data(parsed_data)

        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse AI response as JSON: {str(e)}")
            st.text("Raw response:")
            st.code(response_text)
            return self._create_empty_structure()
        except Exception as e:
            st.warning(f"Error processing AI response: {str(e)}")
            return self._create_empty_structure()

    def _validate_parsed_data(self, data: dict):
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
        return {
            "name": "",
            "email": "",
            "phone": "",
            "skills": [],
            "experience": [],
            "education": [],
            "summary": ""
        }



