import PyPDF2
import streamlit as st
from io import BytesIO

class PDFProcessor:
    """Handles PDF text extraction without OCR"""
    
    def __init__(self):
        """Initialize PDF processor"""
        pass
    
    def extract_text_from_pdf(self, uploaded_file):
        """
        Extract text from PDF file using PyPDF2
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        try:
            # Read the uploaded file content
            file_content = uploaded_file.read()
            
            # Create a BytesIO object from the file content
            file_like_object = BytesIO(file_content)
            
            # Create PDF reader
            pdf_reader = PyPDF2.PdfReader(file_like_object)
            
            # Extract text from all pages
            text_content = []
            
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text.strip():
                        text_content.append(page_text.strip())
                        
                except Exception as page_error:
                    st.warning(f"Could not extract text from page {page_num + 1}: {str(page_error)}")
                    continue
            
            # Join all text with newlines
            extracted_text = '\n'.join(text_content)
            
            if not extracted_text.strip():
                st.warning("No text could be extracted from this PDF.")
                
            return extracted_text
            
        except Exception as e:
            st.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def process_pdf_file(self, uploaded_file):
        """
        Process PDF file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        return self.extract_text_from_pdf(uploaded_file)

