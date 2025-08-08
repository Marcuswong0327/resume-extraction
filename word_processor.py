import docx
import streamlit as st
from io import BytesIO

class WordProcessor:
    """Handles Word document text extraction"""
    
    def __init__(self):
        pass
    
    def extract_text(self, uploaded_file):
        """
        Extract text from Word document
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text as string
        """
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Read file content
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset for potential future use
            
            if not file_content:
                raise ValueError("Word file is empty or could not be read")
            
            # Create a BytesIO object from the file content
            file_stream = BytesIO(file_content)
            
            # Load the document
            try:
                doc = docx.Document(file_stream)
            except Exception as e:
                raise ValueError(f"Invalid Word document format: {str(e)}")
            
            # Extract text from all paragraphs
            text_content = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:  # Only add non-empty paragraphs
                    text_content.append(text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            # Join all text with newlines
            extracted_text = "\n".join(text_content)
            
            if not extracted_text.strip():
                raise ValueError("No text content found in Word document")
            
            return extracted_text
            
        except Exception as e:
            error_msg = f"Error extracting text from Word document: {str(e)}"
            st.error(error_msg)
            raise Exception(error_msg)
    
    def extract_text_with_formatting(self, uploaded_file):
        """
        Extract text with basic formatting information
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Dictionary with text and formatting information
        """
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Create a BytesIO object from the file content
            file_stream = BytesIO(file_content)
            doc = docx.Document(file_stream)
            
            formatted_content = {
                "text": "",
                "paragraphs": [],
                "tables": []
            }
            
            # Extract paragraphs with formatting
            for paragraph in doc.paragraphs:
                para_info = {
                    "text": paragraph.text.strip(),
                    "style": paragraph.style.name if paragraph.style else "Normal",
                    "runs": []
                }
                
                for run in paragraph.runs:
                    run_info = {
                        "text": run.text,
                        "bold": run.bold,
                        "italic": run.italic,
                        "underline": run.underline
                    }
                    para_info["runs"].append(run_info)
                
                if para_info["text"]:
                    formatted_content["paragraphs"].append(para_info)
            
            # Extract tables
            for table_idx, table in enumerate(doc.tables):
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        row_data.append(cell.text.strip())
                    table_data.append(row_data)
                
                formatted_content["tables"].append({
                    "index": table_idx,
                    "data": table_data
                })
            
            # Combine all text
            all_text = []
            for para in formatted_content["paragraphs"]:
                all_text.append(para["text"])
            
            for table in formatted_content["tables"]:
                for row in table["data"]:
                    all_text.append(" | ".join(row))
            
            formatted_content["text"] = "\n".join(all_text)
            
            return formatted_content
            
        except Exception as e:
            st.error(f"Error extracting formatted text from Word document: {str(e)}")
            # Fallback to simple text extraction
            return {"text": self.extract_text(uploaded_file), "paragraphs": [], "tables": []}
