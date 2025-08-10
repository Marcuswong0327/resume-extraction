import re
from typing import Dict, List, Any
import streamlit as st

class DataExtractor:
    """Combines OCR results with AI parsing for comprehensive data extraction"""
    
    def __init__(self):
        # Regular expressions for fallback extraction
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_patterns = [
            re.compile(r'\b0\d{3}\s*\d{3}\s*\d{3}\b'),  # 0123 456 789 (Australian mobile)
            re.compile(r'\b\+61\s*\d{3}\s*\d{3}\s*\d{3}\b'),  # +61 123 456 789
            re.compile(r'\b04\d{2}\s*\d{3}\s*\d{3}\b'),  # 04XX XXX XXX (Australian mobile)
            re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # 123-456-7890
            re.compile(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b'),  # (123) 456-7890
            re.compile(r'\b\d{3}\.\d{3}\.\d{4}\b'),  # 123.456.7890
            re.compile(r'\b\d{10}\b'),  # 1234567890
            re.compile(r'\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}'),  # +1 123 456 7890
            re.compile(r'\b0\d{9}\b'),  # 0123456789 (10 digit Australian)
            re.compile(r'\b06\d\s*\d{3}\s*\d{4}\b'),  # 060 XXX XXXX (South African format from sample)
        ]
    
    def extract_candidate_info(self, raw_text: str, ai_parsed_data: Dict, filename: str) -> Dict[str, Any]:
        """
        Extract and combine candidate information from OCR text and AI parsing
        
        Args:
            raw_text: Raw text from OCR/Word extraction (concatenated from all pages)
            ai_parsed_data: Structured data from AI parsing
            filename: Source filename
            
        Returns:
            Combined candidate information dictionary
        """
        try:
            # Start with AI parsed data
            candidate_info = ai_parsed_data.copy() if ai_parsed_data else {}
            candidate_info["filename"] = filename
            candidate_info["raw_text"] = raw_text
            
            # ALWAYS apply regex fallback for critical information (emails and phones)
            # This ensures we capture information even if AI misses it
            candidate_info = self._apply_comprehensive_fallback_extraction(candidate_info, raw_text)
            
            # Clean and validate extracted data
            candidate_info = self._clean_extracted_data(candidate_info)
            
            return candidate_info
            
        except Exception as e:
            st.error(f"Error extracting candidate information: {str(e)}")
            return self._create_fallback_candidate_info(raw_text, filename)
    
    def _apply_comprehensive_fallback_extraction(self, candidate_info: Dict, raw_text: str) -> Dict:
    # Extract email
        ai_email = candidate_info.get("email", "").strip()
        regex_emails = self.email_pattern.findall(raw_text)

        if regex_emails:
            if not ai_email or "@" not in ai_email:
                candidate_info["email"] = regex_emails[0]
            elif ai_email not in regex_emails:
                candidate_info["email"] = ai_email
        elif ai_email:
            candidate_info["email"] = ai_email

        # ===== Modified phone number extraction =====
        ai_phone = candidate_info.get("phone", "").strip()
        regex_phone = None

        # Step 1: Try to extract phone near the candidate's email (header area)
        email_to_search = candidate_info.get("email", "")
        if email_to_search:
            # Search within ~150 characters after the email
            email_pos = raw_text.find(email_to_search)
            if email_pos != -1:
                contact_block = raw_text[email_pos: email_pos + 150]  # capture header block
                for pattern in self.phone_patterns:
                    phone_matches = pattern.findall(contact_block)
                    if phone_matches:
                        regex_phone = phone_matches[0]
                        break

        # Step 2: If not found near email, search entire document (fallback)
        if not regex_phone:
            for pattern in self.phone_patterns:
                phone_matches = pattern.findall(raw_text)
                if phone_matches:
                    regex_phone = phone_matches[0]
                    break

        if regex_phone:
            if not ai_phone or len(ai_phone.replace(" ", "").replace("-", "")) < 8:
                candidate_info["phone"] = regex_phone
            else:
                candidate_info["phone"] = ai_phone
        elif ai_phone:
            candidate_info["phone"] = ai_phone

        # Extract name if missing
        if not candidate_info.get("first_name") and not candidate_info.get("family_name"):
            names = self._extract_names_fallback(raw_text)
            if names:
                candidate_info["first_name"] = names.get("first_name", "")
                candidate_info["family_name"] = names.get("family_name", "")

        # Extract job title if missing
        if not candidate_info.get("job_title"):
            job_title = self._extract_job_title_fallback(raw_text)
            if job_title:
                candidate_info["job_title"] = job_title

        return candidate_info

    def _extract_names_fallback(self, text: str) -> Dict[str, str]:
        """
        Extract first and family names using heuristics
        
        Args:
            text: Raw text to extract names from
            
        Returns:
            Dictionary with first_name and family_name
        """
        try:
            lines = text.split('\n')
            
            # Look for name in first few lines
            for line in lines[:10]:
                line = line.strip()
                
                # Skip empty lines and common header words
                if not line or any(word in line.lower() for word in 
                                 ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'page', 'contact']):
                    continue
                
                # Look for lines with 2-4 words that could be a name
                words = line.split()
                if 2 <= len(words) <= 4:
                    # Check if words look like names (start with capital letters)
                    if all(word[0].isupper() and word.replace('.', '').replace(',', '').isalpha() 
                          for word in words if len(word) > 1):
                        # Assume first word is first name, last word is family name
                        return {
                            "first_name": words[0],
                            "family_name": words[-1]
                        }
            
            return {"first_name": "", "family_name": ""}
            
        except Exception:
            return {"first_name": "", "family_name": ""}
    
    def _extract_job_title_fallback(self, text: str) -> str:
        """
        Extract job title using pattern matching
        
        Args:
            text: Raw text to extract job title from
            
        Returns:
            Extracted job title or empty string
        """
        try:
            # Common job title patterns and keywords
            job_patterns = [
                r'(?:position|title|role|job)\s*:?\s*([^.\n]+)',
                r'(?:current|present)\s+(?:position|title|role)\s*:?\s*([^.\n]+)',
                r'(?:working as|employed as)\s+([^.\n]+)',
            ]
            
            # Common job titles to look for (expanded for warehouse, logistics, and management roles)
            job_titles = [
                # Management and Operations
                'operations manager', 'warehouse manager', 'sales manager', 'general manager',
                'logistics coordinator', 'warehouse supervisor', 'receiving supervisor',
                'production manager', 'inventory team lead', 'team leader', 'supervisor',
                'logistics manager', 'supply chain manager', 'distribution manager',
                
                # Warehouse and Logistics
                'warehouse team member', 'forklift operator', 'warehouse coordinator',
                'inventory coordinator', 'shipping coordinator', 'receiving coordinator',
                'pick packer', 'warehouse associate', 'logistics coordinator',
                'warehouse inventory team lead', 'fabric processor', 'cd packer',
                
                # Customer Service and Sales
                'customer service officer', 'sales representative', 'account manager',
                'customer service manager', 'client servicing consultant', 'sales manager',
                'business development consultant', 'key account manager',
                
                # Technical and Data
                'data scientist', 'software engineer', 'software developer', 'web developer',
                'data analyst', 'research programmer', 'analyst programmer',
                'systems analyst', 'business analyst', 'research fellow',
                
                # Other roles from samples
                'waitress', 'kitchen hand', 'retail associate', 'office manager',
                'administration officer', 'merchandising', 'security officer'
            ]
            
            text_lower = text.lower()
            
            # Try pattern matching first
            for pattern in job_patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    title = match.group(1).strip()
                    if title and len(title) < 100:  # Reasonable length check
                        return title.title()
            
            # Look for common job titles
            for title in job_titles:
                if title in text_lower:
                    # Try to extract the full title with context
                    title_pattern = rf'\b([^.\n]*{re.escape(title)}[^.\n]*)\b'
                    match = re.search(title_pattern, text_lower)
                    if match:
                        extracted_title = match.group(1).strip()
                        if len(extracted_title) < 100:
                            return extracted_title.title()
                    else:
                        return title.title()
            
            return ""
            
        except Exception:
            return ""
    
    def _clean_extracted_data(self, candidate_info: Dict) -> Dict:
        """
        Clean and validate extracted data
        
        Args:
            candidate_info: Raw candidate information
            
        Returns:
            Cleaned candidate information
        """
        # Clean email
        email = candidate_info.get("email", "").strip()
        if email and not self.email_pattern.match(email):
            candidate_info["email"] = ""
        
        # Clean phone number
        phone = candidate_info.get("phone", "").strip()
        if phone:
            # Remove common formatting and keep only valid phone patterns
            cleaned_phone = re.sub(r'[^\d\-\(\)\.\+\s]', '', phone)
            candidate_info["phone"] = cleaned_phone
        
        # Clean names
        first_name = candidate_info.get("first_name", "").strip()
        if first_name:
            candidate_info["first_name"] = first_name.title()
        
        family_name = candidate_info.get("family_name", "").strip()
        if family_name:
            candidate_info["family_name"] = family_name.title()
        
        # Clean job title
        job_title = candidate_info.get("job_title", "").strip()
        if job_title:
            candidate_info["job_title"] = job_title.title()
        
        # Ensure all required fields exist
        required_fields = ["first_name", "family_name", "email", "phone", "job_title"]
        for field in required_fields:
            if field not in candidate_info:
                candidate_info[field] = ""
        
        return candidate_info
    
    def _create_fallback_candidate_info(self, raw_text: str, filename: str) -> Dict:
        """
        Create fallback candidate info when AI parsing fails completely
        
        Args:
            raw_text: Raw text from document
            filename: Source filename
            
        Returns:
            Basic candidate information dictionary
        """
        fallback_info = {
            "first_name": "",
            "family_name": "",
            "email": "",
            "phone": "",
            "job_title": "",
            "filename": filename,
            "raw_text": raw_text
        }
        
        # Try to extract basic information using regex
        fallback_info = self._apply_fallback_extraction(fallback_info, raw_text)
        fallback_info = self._clean_extracted_data(fallback_info)
        
        return fallback_info


