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
        if not resume_text or not resume_text.strip():
            return self._create_empty_structure()
            
        # Create prompt for resume parsing
        prompt = self._create_batch_prompt(resume_text)
            
        # Make API call to DeepSeek with retries
        response = self._make_api_call_with_retry(prompt)
            
        if response:
            return self._parse_batch_api_response(response, expected_count = 1)
        else:
            return self._create_empty_structure()

    def parse_resume_batch(self, resume_text):
        try:
            if not resume_text:
                return[]
            # Build prompt with multiple resumes 
            prompt = self._create_batch_prompt(resume_text)

            #Call API 
            response = self._make_api_call_with_retry(prompt)
            if response: 
                return self._parse_batch_api_response(response, expected_count = len(resume_text))
            else: 
                return [self._create_empty_structure() for _ in resume_text] 
        except Exception as e:
            st.error(f"Error parsing batch resumes: {str(e)}")
            return [self._create_empty_structure() for _ in resume_text]

    def _create_batch_prompt(self, resume_texts):
        """
        Create a structured prompt for resume parsing
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Formatted prompt string
        """
        # Truncate text if too long to avoid token limits
        max_chars = 15000
        truncated_resumes = [] 
        for i, text in enumerate(resume_texts, start=1):
            if len(text) > max_chars:
                text = text[:max_chars] + "..." 
            truncated_resumes.append(f"Resume {i}:\n{text}\n")
        
        prompt = f"""
You are a strict JSON generator for resume parsing. Do not include any explanations or markdown. Output must be valid JSON only.

INPUT_RESUMES (ordered):
{RESUME_BLOCK}

TASK
For each resume, extract the following fields:
- first_name
- last_name
- mobile
- email
- current_job_title
- current_company
- previous_job_title
- previous_company

OUTPUT REQUIREMENTS
1) Return a **JSON array** with length = {N}, where N is the number of input resumes.
2) The i-th array item corresponds to Resume i (same order).
3) Keys must be EXACTLY these (snake_case). No extra keys.
4) All values must be strings. If unknown, use "".
5) Do NOT wrap the JSON in code fences or add prose.

DISAMBIGUATION RULES
- Name splitting: if the full name has >= 2 tokens, first_name = first token, last_name = the rest (unchanged). If only one token, first_name = token, last_name = "".
- Mobile: return the first plausible phone number found (prefer header/top of first page if present). Keep original formatting.
- Email: return the first valid email found.
- Current vs previous roles: the job with the most recent end date (or ongoing markers like "Present", "Current", "Now") is current. The chronologically prior job is previous. If only one job exists, fill current_* and leave previous_* empty.

OUTPUT JSON EXAMPLE (shape only; values are examples):
[
  {
    "first_name": "Alicia",
    "last_name": "Tan Li Mei",
    "mobile": "+60123456789",
    "email": "alicia.tan@example.com",
    "current_job_title": "Software Engineer",
    "current_company": "Grab",
    "previous_job_title": "Intern",
    "previous_company": "Petronas"
  }
]

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
    
    def _parse_batch_api_response(self, response_text, expected_count):
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

            data = json.loads(response_text)

            #Normalize response into a flat list of dicts
            if isinstance(data, dict):
                data = [data] # single dict into list 
            elif isinstance(data, list):
                #Flatten nested list into one level 
                flattened = []
                for item in data: 
                    if isinstance(item, list):
                        flattened.append(item[0] if item else{}) 
                    else: 
                        flattened.append(item) 
                data = flattened 
            else: 
                data = [{} for _ in range(expected_count)]


            # Ensure exactly expected_count items 
            results = []
            for i in range(expected_count): 
                item = data[i] if i < len(data) else{}
                results.append(self._validate_parsed_data(item))
            return results 
            
        except Exception as e: 
            st.warning(f"Error parsing batch API response: {str(e)}")
            st.code(response_text) 
            return [self._create_empty_structure() for _ in range(expected_count)]

    
    def _validate_parsed_data(self, data):
    # Unwrap nested lists until we get a dict or empty
        while isinstance(data, list) and data:
            data = data[0] 

        if not isinstance(data, dict):
            data = {}

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
