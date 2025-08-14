import re
from typing import Dict, List, Any
import streamlit as st

class DataExtractor:
    """Combines OCR results with AI parsing for comprehensive data extraction"""
    
    def __init__(self):
        # Regular expressions for fallback extraction
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_patterns = [
            re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # 123-456-7890
            re.compile(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b'),  # (123) 456-7890
            re.compile(r'\b\d{3}\.\d{3}\.\d{4}\b'),  # 123.456.7890
            re.compile(r'\b\d{10}\b'),  # 1234567890
            re.compile(r'\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}'),  # +1 123 456 7890
        ]
    
    def extract_candidate_info(self, raw_text: str, ai_parsed_data: Dict, filename: str) -> Dict[str, Any]:
        """
        Extract and combine candidate information from OCR text and AI parsing
        
        Args:
            raw_text: Raw text from OCR
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
            
            # Apply fallback extraction for missing critical information
            candidate_info = self._apply_fallback_extraction(candidate_info, raw_text)
            
            # Clean and validate extracted data
            candidate_info = self._clean_extracted_data(candidate_info)
            
            # Enhance skills extraction
            candidate_info["skills"] = self._enhance_skills_extraction(
                candidate_info.get("skills", []), 
                raw_text
            )
            
            # Format experience and education for better display
            candidate_info["experience_formatted"] = self._format_experience(
                candidate_info.get("experience", [])
            )
            candidate_info["education_formatted"] = self._format_education(
                candidate_info.get("education", [])
            )
            
            return candidate_info
            
        except Exception as e:
            st.error(f"Error extracting candidate information: {str(e)}")
            return self._create_fallback_candidate_info(raw_text, filename)
    
    def _apply_fallback_extraction(self, candidate_info: Dict, raw_text: str) -> Dict:
        """
        Apply regex-based fallback extraction for missing information
        
        Args:
            candidate_info: Existing candidate information
            raw_text: Raw text to extract from
            
        Returns:
            Enhanced candidate information
        """
        # Extract email if missing
        if not candidate_info.get("email"):
            email_matches = self.email_pattern.findall(raw_text)
            if email_matches:
                candidate_info["email"] = email_matches[0]
        
        # Extract phone if missing
        if not candidate_info.get("phone"):
            for pattern in self.phone_patterns:
                phone_matches = pattern.findall(raw_text)
                if phone_matches:
                    candidate_info["phone"] = phone_matches[0]
                    break
        
        # Extract name if missing (simple heuristic)
        if not candidate_info.get("name"):
            candidate_info["name"] = self._extract_name_fallback(raw_text)
        
        return candidate_info
    
    def _extract_name_fallback(self, text: str) -> str:
        """
        Extract candidate name using heuristics
        
        Args:
            text: Raw text to extract name from
            
        Returns:
            Extracted name or empty string
        """
        try:
            lines = text.split('\n')
            
            # Look for name in first few lines
            for line in lines[:10]:  # Increased search range
                line = line.strip()
                
                # Skip empty lines and common header words
                if not line or any(word in line.lower() for word in 
                                 ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'page', 'contact']):
                    continue
                
                # Look for lines with 2-4 words that could be a name
                words = line.split()
                if 2 <= len(words) <= 4:
                    # Check if words look like names (start with capital letters)
                    if all(word[0].isupper() and word.replace('.', '').isalpha() for word in words if len(word) > 1):
                        return line
                
                # Single word that might be a name (less reliable)
                if len(words) == 1 and len(words[0]) > 2 and words[0][0].isupper() and words[0].isalpha():
                    # Look for a last name in the next lines
                    for next_line in lines[lines.index(line)+1:lines.index(line)+3]:
                        next_words = next_line.strip().split()
                        if len(next_words) == 1 and next_words[0][0].isupper() and next_words[0].isalpha():
                            return f"{words[0]} {next_words[0]}"
            
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
        
        # Clean name
        name = candidate_info.get("name", "").strip()
        if name:
            # Remove extra whitespace and capitalize properly
            candidate_info["name"] = ' '.join(word.capitalize() for word in name.split())
        
        # Ensure required fields exist
        for field in ["skills", "experience", "education"]:
            if field not in candidate_info:
                candidate_info[field] = []
        
        return candidate_info
    
    def _enhance_skills_extraction(self, existing_skills: List[str], raw_text: str) -> List[str]:
        """
        Enhance skills extraction with additional pattern matching
        
        Args:
            existing_skills: Skills already extracted by AI
            raw_text: Raw text to search for additional skills
            
        Returns:
            Enhanced skills list
        """
        # Common technical skills and keywords to look for
        common_skills = [
            # Programming languages
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
            'TypeScript', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'SQL', 'C',
            
            # Web technologies
            'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express',
            'Django', 'Flask', 'Spring', 'Laravel', 'WordPress', 'Bootstrap',
            
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Oracle', 'Redis',
            'Elasticsearch', 'Cassandra', 'DynamoDB',
            
            # Cloud platforms
            'AWS', 'Azure', 'Google Cloud', 'GCP', 'Docker', 'Kubernetes',
            'Jenkins', 'Git', 'GitHub', 'GitLab', 'Terraform',
            
            # Data science
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'Pandas', 'NumPy', 'Scikit-learn', 'Jupyter', 'Apache Spark',
            
            # Other tools and frameworks
            'Excel', 'PowerBI', 'Tableau', 'Photoshop', 'Illustrator',
            'AutoCAD', 'Solidworks', 'JIRA', 'Agile', 'Scrum', 'DevOps',
            'REST API', 'GraphQL', 'Microservices', 'Linux', 'Windows'
        ]
        
        enhanced_skills = list(existing_skills) if existing_skills else []
        
        # Look for additional skills in the text
        text_upper = raw_text.upper()
        for skill in common_skills:
            skill_variants = [skill, skill.lower(), skill.upper()]
            
            for variant in skill_variants:
                if variant.upper() in text_upper and skill not in enhanced_skills:
                    # Check if it's a whole word match
                    if re.search(r'\b' + re.escape(variant.upper()) + r'\b', text_upper):
                        enhanced_skills.append(skill)
                        break
        
        # Remove duplicates and empty entries
        enhanced_skills = list(set(skill.strip() for skill in enhanced_skills if skill.strip()))
        
        return sorted(enhanced_skills)
    
    def _format_experience(self, experience_list: List) -> List[str]:
        """
        Format experience data for display
        
        Args:
            experience_list: List of experience dictionaries or strings
            
        Returns:
            List of formatted experience strings
        """
        formatted_experience = []
        
        for exp in experience_list:
            if isinstance(exp, dict):
                parts = []
                
                position = exp.get("position", "").strip()
                company = exp.get("company", "").strip()
                duration = exp.get("duration", "").strip()
                description = exp.get("description", "").strip()
                
                if position and company:
                    parts.append(f"{position} at {company}")
                elif position:
                    parts.append(position)
                elif company:
                    parts.append(company)
                
                if duration:
                    parts.append(f"({duration})")
                
                if description:
                    # Truncate long descriptions
                    if len(description) > 200:
                        description = description[:200] + "..."
                    parts.append(f"- {description}")
                
                if parts:
                    formatted_experience.append(" ".join(parts))
            elif isinstance(exp, str) and exp.strip():
                formatted_experience.append(exp.strip())
        
        return formatted_experience
    
    def _format_education(self, education_list: List) -> List[str]:
        """
        Format education data for display
        
        Args:
            education_list: List of education dictionaries or strings
            
        Returns:
            List of formatted education strings
        """
        formatted_education = []
        
        for edu in education_list:
            if isinstance(edu, dict):
                parts = []
                
                degree = edu.get("degree", "").strip()
                field = edu.get("field", "").strip()
                institution = edu.get("institution", "").strip()
                year = edu.get("year", "").strip()
                
                if degree and field:
                    parts.append(f"{degree} in {field}")
                elif degree:
                    parts.append(degree)
                elif field:
                    parts.append(field)
                
                if institution:
                    parts.append(f"from {institution}")
                
                if year:
                    parts.append(f"({year})")
                
                if parts:
                    formatted_education.append(" ".join(parts))
            elif isinstance(edu, str) and edu.strip():
                formatted_education.append(edu.strip())
        
        return formatted_education
    
    def _create_fallback_candidate_info(self, raw_text: str, filename: str) -> Dict:
        """
        Create basic candidate info when AI parsing fails
        
        Args:
            raw_text: Raw text from OCR
            filename: Source filename
            
        Returns:
            Basic candidate information dictionary
        """
        candidate_info = {
            "filename": filename,
            "raw_text": raw_text,
            "name": self._extract_name_fallback(raw_text),
            "email": "",
            "phone": "",
            "skills": [],
            "experience": [],
            "education": [],
            "summary": "",
            "experience_formatted": [],
            "education_formatted": []
        }
        
        # Apply basic regex extraction
        return self._apply_fallback_extraction(candidate_info, raw_text)
