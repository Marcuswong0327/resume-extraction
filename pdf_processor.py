import PyPDF2
import streamlit as st
from io import BytesIO
import logging

# Alternative PDF processing libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class PDFProcessor:
    """Enhanced PDF text extraction with multiple fallback methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_text_from_pdf(self, uploaded_file):
        """
        Extract text from PDF file using multiple methods with fallbacks
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        
        # Try multiple extraction methods
        methods = [
            ("PyPDF2", self._extract_with_pypdf2),
        ]
        
        if PDFPLUMBER_AVAILABLE:
            methods.append(("pdfplumber", self._extract_with_pdfplumber))
            
        if PYMUPDF_AVAILABLE:
            methods.append(("PyMuPDF", self._extract_with_pymupdf))
        
        for method_name, method_func in methods:
            try:
                self.logger.info(f"Trying {method_name} for {uploaded_file.name}")
                text = method_func(file_content)
                
                if text and text.strip() and len(text.strip()) > 50:
                    self.logger.info(f"Successfully extracted {len(text)} characters using {method_name}")
                    return text
                else:
                    self.logger.warning(f"{method_name} extracted insufficient text ({len(text) if text else 0} chars)")
                    
            except Exception as e:
                self.logger.error(f"{method_name} failed: {str(e)}")
                continue
        
        # If all methods fail
        st.error(f"❌ All PDF extraction methods failed for {uploaded_file.name}")
        return ""
    
    def _extract_with_pypdf2(self, file_content):
        """Extract text using PyPDF2"""
        file_like_object = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(file_like_object)
        
        text_content = []
        
        for page_num in range(len(pdf_reader.pages)):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text_content.append(page_text.strip())
                    
            except Exception as page_error:
                self.logger.warning(f"PyPDF2 failed on page {page_num + 1}: {str(page_error)}")
                continue
        
        return '\n'.join(text_content)
    
    def _extract_with_pdfplumber(self, file_content):
        """Extract text using pdfplumber (fallback method)"""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available")
            
        file_like_object = BytesIO(file_content)
        text_content = []
        
        with pdfplumber.open(file_like_object) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(page_text.strip())
                except Exception as page_error:
                    self.logger.warning(f"pdfplumber failed on page {page_num + 1}: {str(page_error)}")
                    continue
        
        return '\n'.join(text_content)
    
    def _extract_with_pymupdf(self, file_content):
        """Extract text using PyMuPDF (fallback method)"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not available")
            
        file_like_object = BytesIO(file_content)
        text_content = []
        
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        
        for page_num in range(pdf_document.page_count):
            try:
                page = pdf_document[page_num]
                page_text = page.get_text()
                
                if page_text and page_text.strip():
                    text_content.append(page_text.strip())
                    
            except Exception as page_error:
                self.logger.warning(f"PyMuPDF failed on page {page_num + 1}: {str(page_error)}")
                continue
        
        pdf_document.close()
        return '\n'.join(text_content)
    
    def process_pdf_file(self, uploaded_file):
        """
        Process PDF file with enhanced error handling
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        try:
            if uploaded_file.size == 0:
                self.logger.error(f"PDF file {uploaded_file.name} is empty")
                return ""
                
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
                self.logger.error(f"PDF file {uploaded_file.name} is too large ({uploaded_file.size} bytes)")
                st.error(f"❌ File {uploaded_file.name} is too large (max 50MB)")
                return ""
                
            return self.extract_text_from_pdf(uploaded_file)
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {uploaded_file.name}: {str(e)}")
            st.error(f"❌ Error processing PDF {uploaded_file.name}: {str(e)}")
            return ""
