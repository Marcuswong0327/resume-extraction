import requests
import json
import streamlit as st

class AIParser:
    """Handles DeepSeek V3 API integration for intelligent resume parsing"""
    
    def __init__(self, api_key):
        """
        Initialize AI parser with DeepSeek API key
        
        Args:
            api_key: DeepSeek V3 API key
        """
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def parse_resume(self, resume_text):
        """
        Parse resume text using DeepSeek V3 API
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            Structured resume data as dictionary
        """
        try:
            # Create prompt for resume parsing
            prompt = self._create_parsing_prompt(resume_text)
            
            # Make API call to DeepSeek
            response = self._make_api_call(prompt)
            
            if response:
                return self._parse_api_response(response)
            else:
                return self._create_empty_structure()
                
        except Exception as e:
            st.error(f"Error parsing resume with AI: {str(e)}")
            return self._create_empty_structure()
    
    def _create_parsing_prompt(self, resume_text):
        """
        Create a structured prompt for resume parsing
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Formatted prompt string
        """
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
            "description": "job description"
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
3. Extract skills from skills sections, job descriptions, and throughout the resume
4. Include all work experience entries found
5. Include all education entries found
6. Be thorough and accurate in extraction
"""
        return prompt
    
    def _make_api_call(self, prompt):
        """
        Make API call to DeepSeek V3
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            API response content or None
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                st.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Network error calling DeepSeek API: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error calling DeepSeek API: {str(e)}")
            return None
    
    def _parse_api_response(self, response_text):
        """
        Parse API response and extract JSON data
        
        Args:
            response_text: Raw response text from API
            
        Returns:
            Parsed JSON data as dictionary
        """
        try:
            # Try to find JSON in the response
            response_text = response_text.strip()
            
            # Remove any markdown code block markers
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(response_text)
            
            # Validate structure
            return self._validate_parsed_data(parsed_data)
            
        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse AI response as JSON: {str(e)}")
            return self._create_empty_structure()
        except Exception as e:
            st.warning(f"Error processing AI response: {str(e)}")
            return self._create_empty_structure()
    
    def _validate_parsed_data(self, data):
        """
        Validate and clean parsed data structure
        
        Args:
            data: Parsed data dictionary
            
        Returns:
            Validated and cleaned data dictionary
        """
        # Ensure all required fields exist
        validated_data = {
            "name": str(data.get("name", "")).strip(),
            "email": str(data.get("email", "")).strip(),
            "phone": str(data.get("phone", "")).strip(),
            "skills": [],
            "experience": [],
            "education": [],
            "summary": str(data.get("summary", "")).strip()
        }
        
        # Validate skills array
        if isinstance(data.get("skills"), list):
            validated_data["skills"] = [str(skill).strip() for skill in data["skills"] if str(skill).strip()]
        
        # Validate experience array
        if isinstance(data.get("experience"), list):
            for exp in data["experience"]:
                if isinstance(exp, dict):
                    validated_exp = {
                        "company": str(exp.get("company", "")).strip(),
                        "position": str(exp.get("position", "")).strip(),
                        "duration": str(exp.get("duration", "")).strip(),
                        "description": str(exp.get("description", "")).strip()
                    }
                    if any(validated_exp.values()):  # Only add if at least one field has content
                        validated_data["experience"].append(validated_exp)
        
        # Validate education array
        if isinstance(data.get("education"), list):
            for edu in data["education"]:
                if isinstance(edu, dict):
                    validated_edu = {
                        "institution": str(edu.get("institution", "")).strip(),
                        "degree": str(edu.get("degree", "")).strip(),
                        "field": str(edu.get("field", "")).strip(),
                        "year": str(edu.get("year", "")).strip()
                    }
                    if any(validated_edu.values()):  # Only add if at least one field has content
                        validated_data["education"].append(validated_edu)
        
        return validated_data
    
    def _create_empty_structure(self):
        """
        Create empty data structure for failed parsing
        
        Returns:
            Empty data structure dictionary
        """
        return {
            "name": "",
            "email": "",
            "phone": "",
            "skills": [],
            "experience": [],
            "education": [],
            "summary": ""
        }
