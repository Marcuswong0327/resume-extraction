import requests
import json
import streamlit as st
import time
import logging
import os
from concurrent.futures import ThreadPoolExecutor

class AIParser:
    """Enhanced DeepSeek V3 API integration with improved error handling and debugging"""
    
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
            "HTTP-Referer": "https://replit.com",
            "X-Title": "Resume Parser"
        }
        
        self.logger = logging.getLogger(__name__)
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
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
                error_detail = ""
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text
                raise Exception(f"API test failed: {response.status_code} - {error_detail}")
                
            self.logger.info("OpenRouter API connection test successful")
                
        except Exception as e:
            self.logger.error(f"OpenRouter API connection test failed: {str(e)}")
            raise Exception(f"OpenRouter API connection test failed: {str(e)}")
    
    def parse_resume(self, resume_text, filename="unknown"):
        """
        Parse resume text using DeepSeek V3 API with enhanced error handling
        
        Args:
            resume_text: Raw text extracted from resume
            filename: Name of the source file for logging
            
        Returns:
            Structured resume data as dictionary
        """
        if not resume_text or not resume_text.strip():
            self.logger.warning(f"Empty resume text provided for {filename}")
            return self._create_empty_structure()
            
        # Log text stats
        text_length = len(resume_text.strip())
        self.logger.info(f"Processing resume {filename} with {text_length} characters")
        
        if text_length < 50:
            self.logger.warning(f"Resume text too short for {filename}: {text_length} characters")
            return self._create_empty_structure()
            
        # Create prompt for resume parsing
        prompt = self._create_single_prompt(resume_text)
        
        if self.debug_mode:
            st.info(f"🤖 Sending {len(prompt)} character prompt to AI for {filename}")
            
        # Make API call to DeepSeek with retries
        response = self._make_api_call_with_retry(prompt, filename)
            
        if response:
            return self._parse_api_response(response, filename)
        else:
            self.logger.error(f"No response from AI API for {filename}")
            return self._create_empty_structure()

    def parse_resume_batch(self, resume_texts):
        """
        Parse multiple resumes in a single API call
        
        Args:
            resume_texts: List of resume text strings
            
        Returns:
            List of parsed resume data dictionaries
        """
        try:
            if not resume_texts:
                return []
                
            # Filter out empty texts
            valid_texts = [text for text in resume_texts if text and text.strip()]
            
            if not valid_texts:
                self.logger.warning("No valid resume texts in batch")
                return [self._create_empty_structure() for _ in resume_texts]
            
            # Build prompt with multiple resumes 
            prompt = self._create_batch_prompt(valid_texts)

            # Call API 
            response = self._make_api_call_with_retry(prompt, f"batch_{len(valid_texts)}")
            
            if response: 
                return self._parse_batch_api_response(response, expected_count=len(resume_texts))
            else: 
                return [self._create_empty_structure() for _ in resume_texts] 
                
        except Exception as e:
            self.logger.error(f"Error parsing batch resumes: {str(e)}")
            st.error(f"❌ Error parsing batch resumes: {str(e)}")
            return [self._create_empty_structure() for _ in resume_texts]

    def parse_resumes_in_parallel(self, all_resumes, batch_size=3, max_workers=8):
        """
        Parse resumes in parallel with smaller batches and reduced workers for stability
        
        Args:
            all_resumes: List of resume texts
            batch_size: Number of resumes per batch (reduced for stability)
            max_workers: Maximum number of concurrent workers (reduced)
            
        Returns:
            List of parsed resume data
        """
        results = []
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor: 
                futures = [
                    executor.submit(self.parse_resume_batch, all_resumes[i:i+batch_size])
                    for i in range(0, len(all_resumes), batch_size) 
                ]
                
                for i, future in enumerate(futures):
                    try:
                        batch_results = future.result(timeout=120)  # 2 minute timeout per batch
                        results.extend(batch_results)
                        self.logger.info(f"Completed batch {i+1}/{len(futures)}")
                    except Exception as e:
                        self.logger.error(f"Batch {i+1} failed: {str(e)}")
                        # Add empty structures for failed batch
                        batch_start = i * batch_size
                        batch_end = min((i + 1) * batch_size, len(all_resumes))
                        results.extend([self._create_empty_structure() for _ in range(batch_end - batch_start)])
                        
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {str(e)}")
            return [self._create_empty_structure() for _ in all_resumes]
            
        return results 

    def _create_single_prompt(self, resume_text): 
        """Create optimized prompt for single resume parsing"""
        max_chars = 8000  # Further reduced to ensure API stability with larger batches
        if len(resume_text) > max_chars: 
            resume_text = resume_text[:max_chars] + "..."
            
        prompt = f"""Extract resume data as JSON only:

{resume_text}

Return only:
{{
    "first_name": "",
    "last_name": "", 
    "mobile": "",
    "email": "",
    "current_job_title": "",
    "current_company": "",
    "previous_job_title": "", 
    "previous_company": ""
}}

Most recent job = current. Use "" if not found."""
        
        return prompt
    
    def _create_batch_prompt(self, resume_texts):
        """Create optimized prompt for batch resume parsing"""
        max_chars = 10000  # Further reduced for batch processing
        truncated_resumes = [] 
        
        for i, text in enumerate(resume_texts, start=1):
            if len(text) > max_chars:
                text = text[:max_chars] + "..." 
            truncated_resumes.append(f"Resume {i}:\n{text}\n")
        
        prompt = f"""You are an expert resume parser. Extract structured information from these resumes and return ONLY a valid JSON array.

{' '.join(truncated_resumes)}

Return ONLY a JSON array with one object per resume (no markdown, no explanations):
[
    {{
        "first_name": "candidate first name",
        "last_name": "candidate last name",
        "mobile": "phone/mobile number", 
        "email": "email address",
        "current_job_title": "most recent job title",
        "current_company": "most recent company name",
        "previous_job_title": "previous job title",
        "previous_company": "previous company name"
    }}
]

Rules:
1. Return ONLY valid JSON array - no markdown, no explanations
2. One object per resume in order
3. If information not found, use empty string ""
4. Identify current vs previous by dates"""
        
        return prompt
    
    def _make_api_call_with_retry(self, prompt, context, max_retries=2):
        """
        Make API call to DeepSeek V3 with retry logic and better error handling
        """
        for attempt in range(max_retries):
            try:
                response = self._make_api_call(prompt)
                if response:
                    return response
                    
            except Exception as e:
                self.logger.error(f"API attempt {attempt + 1} failed for {context}: {str(e)}")
                
                if attempt == max_retries - 1:
                    st.error(f"❌ AI API failed after {max_retries} attempts for {context}")
                    return None
                else:
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        return None
    
    def _make_api_call(self, prompt):
        """
        Make API call to DeepSeek V3 with improved error handling
        """
        try:
            payload = {
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,  # Minimal tokens for fastest response
                "temperature": 0.05,  # Lower temperature for faster, more consistent responses
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30  # Fast timeout for quick processing
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not content:
                    self.logger.error("Empty content in API response")
                    return None
                    
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
    
    def _parse_api_response(self, response_text, filename="unknown"):
        """Parse single resume API response with better error handling"""
        try:
            # Clean up response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()
            
            # Find JSON content if wrapped in other text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            if self.debug_mode:
                st.text(f"Cleaned response for {filename}:")
                st.code(response_text, language="json")
            
            data = json.loads(response_text)
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]  # Take first item if it's a list
            
            return self._validate_parsed_data(data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed for {filename}: {str(e)}")
            if self.debug_mode:
                st.error(f"❌ JSON parsing failed for {filename}")
                st.code(response_text)
            return self._create_empty_structure()
        except Exception as e:
            self.logger.error(f"Error parsing API response for {filename}: {str(e)}")
            return self._create_empty_structure()
    
    def _parse_batch_api_response(self, response_text, expected_count):
        """Parse batch API response with improved error handling"""
        try:
            # Clean up response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

            data = json.loads(response_text)

            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]  # Convert single dict to list

            # Ensure exactly expected_count items 
            results = []
            for i in range(expected_count): 
                if i < len(data) and isinstance(data[i], dict): 
                    results.append(self._validate_parsed_data(data[i]))
                else: 
                    results.append(self._create_empty_structure())
                    
            return results 
            
        except json.JSONDecodeError as e: 
            self.logger.error(f"Batch JSON parsing failed: {str(e)}")
            if self.debug_mode:
                st.error(f"❌ Batch JSON parsing failed")
                st.code(response_text) 
            return [self._create_empty_structure() for _ in range(expected_count)]
        except Exception as e:
            self.logger.error(f"Error parsing batch API response: {str(e)}")
            return [self._create_empty_structure() for _ in range(expected_count)]
    
    def _validate_parsed_data(self, data):
        """Validate and clean parsed data"""
        if not isinstance(data, dict):
            return self._create_empty_structure()
        
        # Ensure all required fields exist
        required_fields = [
            'first_name', 'last_name', 'mobile', 'email',
            'current_job_title', 'current_company', 
            'previous_job_title', 'previous_company'
        ]
        
        validated_data = {}
        for field in required_fields:
            value = data.get(field, "")
            # Clean the value
            if isinstance(value, str):
                value = value.strip()
            elif value is None:
                value = ""
            else:
                value = str(value).strip()
            validated_data[field] = value
        
        return validated_data
    
    def _create_empty_structure(self):
        """Create empty resume data structure"""
        return {
            'first_name': '',
            'last_name': '',
            'mobile': '',
            'email': '',
            'current_job_title': '',
            'current_company': '',
            'previous_job_title': '',
            'previous_company': ''
        }
