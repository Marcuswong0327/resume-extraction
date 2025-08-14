import docx
import streamlit as st
from io import BytesIO

class WordProcessor:
    """Handles Word document (.doc and .docx) text extraction"""
    
    def __init__(self):
        """Initialize Word processor"""
        pass
    
    def extract_text_from_docx(self, uploaded_file):
        """
        Extract text from DOCX file
        
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
            
            # Load the document
            doc = docx.Document(file_like_object)
            
            # Extract text from all paragraphs
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Extract text from tables if any
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text.strip())
            
            # Join all text with newlines
            extracted_text = '\n'.join(text_content)
            
            return extracted_text
            
        except Exception as e:
            st.error(f"Error extracting text from DOCX file: {str(e)}")
            return ""
    
    def extract_text_from_doc(self, uploaded_file):
        """
        Extract text from DOC file (legacy format)
        Note: This is a simplified implementation
        For better DOC support, consider using python-docx2txt or other libraries
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        try:
            st.warning("DOC files (legacy format) have limited support. Please convert to DOCX for better results.")
            
            # For now, we'll try to read as plain text
            # This is not ideal but provides basic functionality
            file_content = uploaded_file.read()
            try:
                # Try to decode as text (this won't work well for binary DOC files)
                text = file_content.decode('utf-8', errors='ignore')
                return text
            except:
                st.error("Could not extract text from DOC file. Please convert to DOCX format.")
                return ""
                
        except Exception as e:
            st.error(f"Error processing DOC file: {str(e)}")
            return ""
    
    def process_word_file(self, uploaded_file):
        """
        Process Word file (both DOC and DOCX)
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'docx':
                return self.extract_text_from_docx(uploaded_file)
            elif file_extension == 'doc':
                return self.extract_text_from_doc(uploaded_file)
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return ""
                
        except Exception as e:
            st.error(f"Error processing Word file: {str(e)}")
            return ""
