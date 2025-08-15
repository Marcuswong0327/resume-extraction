import requests
import json
import streamlit as st
import time

class AIParser:
    """Handles DeepSeek V3 API integration via OpenRouter for intelligent resume parsing"""
    
    def __init__(self, api_key):
        """
        Initialize AI parser with OpenRouter API key for DeepSeek V3
        
        Args:
            api_key: OpenRouter API key
        """
        if not api_key:
            raise ValueError("OpenRouter API key is required")
            
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replit.com",  # Required by OpenRouter
            "X-Title": "Resume Parser"  # Optional but recommended
        }
        
        # Test the API connection
        self._test_connection()
    
    def _test_connection(self):
        """Test the OpenRouter API connection with DeepSeek V3"""
        try:
            test_payload = {
                "model": "deepseek/deepseek-chat-v3-0324",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"API test failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"OpenRouter API connection test failed: {str(e)}")
    
    def parse_resume(self, resume_text):
        """
        Parse resume text using DeepSeek V3 API
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            Structured resume data as dictionary
        """
        try:
            if not resume_text or not resume_text.strip():
                return self._create_empty_structure()
            
            # Create prompt for resume parsing
            prompt = self._create_parsing_prompt(resume_text)
            
            # Make API call to DeepSeek with retries
            response = self._make_api_call_with_retry(prompt)
            
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
        # Truncate text if too long to avoid token limits
        max_chars = 15000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "..."
        
        prompt = f"""
You are an expert resume parser. Analyze the following resume text and extract structured information in JSON format.

Resume Text:
{resume_text}

Please extract and return ONLY a valid JSON object with the following structure:
sometimes the information maybe on second page. but majority is first page. 
{{
    "first_name": "candidate first name, normally on top few lines of first pages",
    "last_name": "candidate last name, normallly on top few lines of first page",
    "mobile": "phone/mobile number, near around name area",
    "email": "email address, near around mobile phone number area",
    "current_job_title": "current/most recent job title based on latest date, normally the most recent job title will be listed on first",
    "current_company": "current/most recent company name",
    "previous_job_title": "previous job title (before current one), based on the date, normally second job title is before current one",
    "previous_company": "previous company name (before current one)"
}}

Instructions for determining current vs previous positions:
1. Look for dates in the work experience section
2. The position with the most recent dates (or "present", "current", "Now" etc.) is the CURRENT position
3. The position immediately before the current one (chronologically) is the PREVIOUS position
4. If only one job is mentioned, put it as current and leave previous fields as empty
5. Pay attention to date formats like "2020-present", "Jan 2023 - Current", "2022-2024", etc.

Rules:
1. Return ONLY valid JSON, no additional text or explanations
2. If information is not found, use empty string ""
3. Be very careful with dates to correctly identify current vs previous positions
4. Extract full names and split into first_name and last_name
5. Look for mobile/phone numbers in various formats
6. Be thorough and accurate in extraction
"""
        return prompt
    
    def _make_api_call_with_retry(self, prompt, max_retries=3):
        """
        Make API call to DeepSeek V3 with retry logic
        
        Args:
            prompt: Formatted prompt string
            max_retries: Maximum number of retry attempts
            
        Returns:
            API response content or None
        """
        for attempt in range(max_retries):
            try:
                response = self._make_api_call(prompt)
                if response:
                    return response
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"OpenRouter API failed after {max_retries} attempts: {str(e)}")
                    return None
                else:
                    st.warning(f"OpenRouter API attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
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
                "model": "deepseek/deepseek-chat-v3-0324",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 3000,
                "temperature": 0.1,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60  # Increased timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            else:
                error_msg = f"DeepSeek API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            raise Exception("DeepSeek API request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error calling DeepSeek API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling DeepSeek API: {str(e)}")
    
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
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Try to find JSON object in the text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx + 1]
                parsed_data = json.loads(json_text)
            else:
                # Try parsing the entire text
                parsed_data = json.loads(response_text)
            
            # Validate structure
            return self._validate_parsed_data(parsed_data)
            
        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse AI response as JSON: {str(e)}")
            st.text("Raw response:")
            st.code(response_text)
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
            "first_name": str(data.get("first_name", "")).strip(),
            "last_name": str(data.get("last_name", "")).strip(),
            "mobile": str(data.get("mobile", "")).strip(),
            "email": str(data.get("email", "")).strip(),
            "current_job_title": str(data.get("current_job_title", "")).strip(),
            "current_company": str(data.get("current_company", "")).strip(),
            "previous_job_title": str(data.get("previous_job_title", "")).strip(),
            "previous_company": str(data.get("previous_company", "")).strip()
        }
        
        return validated_data
    
    def _create_empty_structure(self):
        """
        Create empty data structure for failed parsing
        
        Returns:
            Empty data structure dictionary
        """
        return {
            "first_name": "",
            "last_name": "",
            "mobile": "",
            "email": "",
            "current_job_title": "",
            "current_company": "",
            "previous_job_title": "",
            "previous_company": ""
        }
