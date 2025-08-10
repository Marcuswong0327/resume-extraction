import fitz  # PyMuPDF
import streamlit as st

class PDFProcessor:
    """Handles PDF text extraction using PyMuPDF"""
    
    def __init__(self):
        pass
    
    def pdf_to_text(self, uploaded_file):
        """
        Extract text from PDF file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            String containing all extracted text
        """
        try:
            uploaded_file.seek(0)
            pdf_bytes = uploaded_file.read()
            uploaded_file.seek(0)  # reset for future use
            
            if not pdf_bytes:
                raise ValueError("PDF file is empty or could not be read")
            
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if len(doc) == 0:
                raise ValueError("No pages found in PDF file")
            
            all_text = []
            for page_num, page in enumerate(doc, start=1):
                try:
                    text = page.get_text()
                    if text.strip():
                        all_text.append(f"--- Page {page_num} ---\n{text}")
                    else:
                        st.warning(f"No text found on page {page_num}")
                except Exception as e:
                    st.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            if not all_text:
                raise ValueError("No text could be extracted from PDF")
            
            return "\n\n".join(all_text)
        
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            raise e
