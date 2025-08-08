import streamlit as st
import pandas as pd
import traceback
import json
from pdf_processor import PDFProcessor
from ocr_service import OCRService
from ai_parser import AIParser
from data_extractor import DataExtractor
from excel_exporter import ExcelExporter

def main():
    st.set_page_config(
        page_title="Resume Parser & Analyzer",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 Resume Parser & Analyzer")

    uploaded_file = st.file_uploader("Upload PDF resume", type=["pdf"])

    if uploaded_file:
        try:
            # Step 1: Extract text from PDF
            pdf_processor = PDFProcessor()
            ocr_service = OCRService()
            ai_parser = AIParser()
            data_extractor = DataExtractor()
            excel_exporter = ExcelExporter()

            with st.spinner("📄 Processing PDF..."):
                extracted_text = pdf_processor.extract_text(uploaded_file)

                # If no text found, use OCR
                if not extracted_text.strip():
                    st.warning("No text found, running OCR...")
                    extracted_text = ocr_service.extract_text(uploaded_file)

            st.success("✅ Text extracted successfully!")

            # Step 2: Send to AI Parser
            with st.spinner("🤖 Parsing with AI..."):
                parsed_data = ai_parser.parse_content(extracted_text)

                # Debugging output
                st.subheader("🔍 Raw AI Parser Output")
                st.json(parsed_data)

            # Step 3: Extract structured data
            with st.spinner("📊 Extracting structured data..."):
                structured_df = data_extractor.extract_to_dataframe(parsed_data)

            st.success("✅ Data extracted successfully!")
            st.dataframe(structured_df)

            # Step 4: Export to Excel
            if st.button("💾 Export to Excel"):
                excel_path = excel_exporter.export(structured_df, "parsed_resume.xlsx")
                st.success(f"Excel file saved: {excel_path}")
                st.download_button(
                    label="Download Excel",
                    data=open(excel_path, "rb"),
                    file_name="parsed_resume.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
