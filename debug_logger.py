import logging
import streamlit as st
import os
from datetime import datetime

class DebugLogger:
    """Comprehensive debugging and logging system for resume processing"""
    
    def __init__(self):
        self.setup_logging()
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_text_extraction(self, filename, text, method):
        """Log text extraction results with validation"""
        text_length = len(text.strip()) if text else 0
        
        if text_length == 0:
            self.logger.warning(f"No text extracted from {filename} using {method}")
            st.warning(f"⚠️ No text extracted from {filename}")
            return False
        
        self.logger.info(f"Extracted {text_length} characters from {filename} using {method}")
        
        if self.debug_mode:
            st.info(f"✅ Extracted {text_length} characters from {filename}")
            with st.expander(f"📄 Debug: View extracted text from {filename}"):
                st.text_area("Extracted Text", text, height=300)
                
        return True
        
    def log_ai_parsing(self, filename, prompt_length, response, parsed_data):
        """Log AI parsing results"""
        self.logger.info(f"AI parsing for {filename} - Prompt: {prompt_length} chars")
        
        if self.debug_mode:
            st.info(f"🤖 AI parsing for {filename}")
            with st.expander(f"🔍 Debug: AI Response for {filename}"):
                st.text("Raw AI Response:")
                st.code(response if response else "No response", language="json")
                st.text("Parsed Data:")
                st.json(parsed_data)
                
        return True
        
    def log_error(self, step, filename, error):
        """Log detailed error information"""
        error_msg = f"Error in {step} for {filename}: {str(error)}"
        self.logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        
        if self.debug_mode:
            with st.expander(f"🐛 Debug: Error details for {filename}"):
                st.code(str(error))
                
    def validate_extracted_text(self, text, filename):
        """Validate extracted text quality"""
        if not text or not text.strip():
            self.log_error("Text Validation", filename, "Empty or whitespace-only text")
            return False
            
        # Check for minimum content
        if len(text.strip()) < 50:
            self.log_error("Text Validation", filename, f"Text too short: {len(text)} characters")
            return False
            
        # Check for common resume indicators
        resume_indicators = ['email', '@', 'phone', 'experience', 'education', 'skills', 'work', 'job']
        text_lower = text.lower()
        found_indicators = [indicator for indicator in resume_indicators if indicator in text_lower]
        
        if len(found_indicators) < 2:
            self.log_error("Text Validation", filename, f"Text doesn't appear to be a resume. Found indicators: {found_indicators}")
            return False
            
        self.logger.info(f"Text validation passed for {filename}. Found indicators: {found_indicators}")
        return True
        
    def enable_debug_mode(self):
        """Enable debug mode for current session"""
        self.debug_mode = True
        st.success("🐛 Debug mode enabled")
        
    def disable_debug_mode(self):
        """Disable debug mode for current session"""
        self.debug_mode = False
        st.info("Debug mode disabled")
