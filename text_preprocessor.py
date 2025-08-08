import re
import streamlit as st

class TextPreprocessor:
    """Handles text cleaning and normalization for better AI parsing"""
    
    def __init__(self):
        pass
    
    def normalize_text(self, text: str) -> str:
        """
        Clean and normalize text for better AI parsing
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Cleaned and normalized text
        """
        try:
            if not text:
                return ""
            
            # Remove excessive newlines and normalize spacing
            text = self._normalize_spacing(text)
            
            # Fix broken words and lines
            text = self._fix_broken_words(text)
            
            # Clean special characters and formatting artifacts
            text = self._clean_artifacts(text)
            
            # Ensure proper spacing around punctuation
            text = self._fix_punctuation_spacing(text)
            
            return text.strip()
            
        except Exception as e:
            st.warning(f"Error normalizing text: {str(e)}")
            return text or ""
    
    def _normalize_spacing(self, text: str) -> str:
        """Remove excessive newlines and normalize spacing"""
        # Replace multiple consecutive newlines with double newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove trailing spaces at line ends
        text = re.sub(r' +\n', '\n', text)
        
        # Remove leading spaces at line starts
        text = re.sub(r'\n +', '\n', text)
        
        return text
    
    def _fix_broken_words(self, text: str) -> str:
        """Fix words that are broken across lines"""
        # Fix hyphenated words broken across lines
        text = re.sub(r'-\s*\n\s*', '', text)
        
        # Fix words broken without hyphens (common in OCR)
        # Look for lowercase letter followed by newline and lowercase letter
        text = re.sub(r'([a-z])\n([a-z])', r'\1\2', text)
        
        return text
    
    def _clean_artifacts(self, text: str) -> str:
        """Clean formatting artifacts and special characters"""
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Clean up bullet points and special formatting
        text = re.sub(r'[•▪▫▪]', '', text)
        
        # Remove page numbers and common header/footer text
        text = re.sub(r'\b(page|pg\.?)\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s*of\s*\d+\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_punctuation_spacing(self, text: str) -> str:
        """Ensure proper spacing around punctuation"""
        # Add space after periods, commas if missing
        text = re.sub(r'([.,])([A-Za-z])', r'\1 \2', text)
        
        # Fix spacing around email @ symbols
        text = re.sub(r'\s+@\s+', '@', text)
        text = re.sub(r'@\s+', '@', text)
        text = re.sub(r'\s+@', '@', text)
        
        # Fix spacing around phone number patterns
        text = re.sub(r'(\d)\s+(\d{3})\s+(\d{3})', r'\1\2 \3', text)
        
        return text
    
    def concatenate_pages_text(self, pages_text: list) -> str:
        """
        Concatenate text from multiple pages with proper formatting
        
        Args:
            pages_text: List of text strings from each page
            
        Returns:
            Concatenated and normalized text
        """
        try:
            if not pages_text:
                return ""
            
            # Join pages with clear page separators
            concatenated = "\n\n=== PAGE BREAK ===\n\n".join(pages_text)
            
            # Normalize the combined text
            normalized = self.normalize_text(concatenated)
            
            return normalized
            
        except Exception as e:
            st.error(f"Error concatenating pages text: {str(e)}")
            return "\n\n".join(pages_text) if pages_text else ""
    
    def extract_sections(self, text: str) -> dict:
        """
        Extract common resume sections for better context
        
        Args:
            text: Full resume text
            
        Returns:
            Dictionary with extracted sections
        """
        try:
            sections = {
                "header": "",
                "contact": "",
                "experience": "",
                "education": "",
                "skills": "",
                "full_text": text
            }
            
            lines = text.split('\n')
            current_section = "header"
            
            # Simple section detection based on common keywords
            for line in lines[:20]:  # Check first 20 lines for header/contact info
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in ['email', 'phone', 'mobile', 'contact']):
                    sections["contact"] += line + "\n"
                elif len(line.strip()) > 0 and current_section == "header":
                    sections["header"] += line + "\n"
            
            return sections
            
        except Exception as e:
            st.warning(f"Error extracting sections: {str(e)}")
            return {"full_text": text, "header": "", "contact": "", "experience": "", "education": "", "skills": ""}
