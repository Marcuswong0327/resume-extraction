import docx
import streamlit as st
from io import BytesIO
import os
import tempfile
import win32com.client as win32


class WordProcessor:
    """Handles Word document (.doc and .docx) text extraction"""

    def __init__(self):
        pass

    def extract_text_from_docx(self, file_path_or_bytes):
        """
        Extract text from DOCX file
        Accepts a file path or BytesIO object
        """
        try:
            if isinstance(file_path_or_bytes, (str, bytes, os.PathLike)):
                doc = docx.Document(file_path_or_bytes)
            else:
                doc = docx.Document(file_path_or_bytes)

            text_content = []

            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text.strip())

            return "\n".join(text_content)

        except Exception as e:
            st.error(f"Error extracting text from DOCX file: {str(e)}")
            return ""

    def convert_doc_to_docx_win32(self, uploaded_file):
        """
        Convert a DOC file to DOCX using Microsoft Word COM Automation (Windows only)
        Returns the path to the converted DOCX file
        """
        try:
            # Save uploaded DOC file to a temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".doc") as tmp_doc:
                tmp_doc.write(uploaded_file.read())
                tmp_doc_path = tmp_doc.name

            tmp_docx_path = tmp_doc_path.replace(".doc", ".docx")

            # Start Word application (hidden)
            word = win32.Dispatch("Word.Application")
            word.Visible = False

            # Open the DOC file
            doc = word.Documents.Open(tmp_doc_path)

            # Save as DOCX (FileFormat=16 is docx)
            doc.SaveAs(tmp_docx_path, FileFormat=16)
            doc.Close()
            word.Quit()

            return tmp_docx_path

        except Exception as e:
            st.error(f"Failed to convert DOC to DOCX using Word: {str(e)}")
            return None

    def process_word_file(self, uploaded_file):
        """
        Process Word file (.doc or .docx) and extract text
        """
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]

            if file_extension == "docx":
                file_content = uploaded_file.read()
                return self.extract_text_from_docx(BytesIO(file_content))

            elif file_extension == "doc":
                st.warning("Converting DOC to DOCX using Microsoft Word...")
                converted_path = self.convert_doc_to_docx_win32(uploaded_file)
                if converted_path and os.path.exists(converted_path):
                    return self.extract_text_from_docx(converted_path)
                else:
                    st.error("Conversion failed. Could not extract text.")
                    return ""

            else:
                st.error(f"Unsupported file format: {file_extension}")
                return ""

        except Exception as e:
            st.error(f"Error processing Word file: {str(e)}")
            return ""
