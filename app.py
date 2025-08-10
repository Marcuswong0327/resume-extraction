import streamlit as st
import pandas as pd
import json
import traceback
import os
from io import BytesIO
from pdf_processor import PDFProcessor
from word_processor import WordProcessor
from ocr_service_fixed import OCRServiceFixed
from ai_parser import AIParser
from data_extractor import DataExtractor
from excel_exporter import ExcelExporter
from text_preprocessor import TextPreprocessor

def main():
    st.set_page_config(
        page_title="Resume Parser & Analyzer",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume Parser & Analyzer")
    st.markdown("Upload multiple PDF and Word resumes to extract candidate information using AI-powered parsing.")
    
    # Initialize session state
    if 'processed_candidates' not in st.session_state:
        st.session_state.processed_candidates = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'processing_in_progress' not in st.session_state:
        st.session_state.processing_in_progress = False
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = None
    
    # Check credentials availability
    credentials_status = check_credentials()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Google Cloud Vision API Configuration
        st.subheader("Google Cloud Vision API")
        with st.expander("API Credentials", expanded=False):
            if credentials_status['gcp_status']:
                st.success("✅ Google Cloud credentials configured")
                if 'GCP_PROJECT_ID' in st.secrets:
                    st.info(f"Project ID: {st.secrets['GCP_PROJECT_ID']}")
            else:
                st.error("❌ Google Cloud credentials not found in secrets")
                st.info("Please add GCP credentials to your secrets.toml file")
        
        # OpenRouter API Configuration
        st.subheader("OpenRouter AI Parser")
        if credentials_status['ai_status']:
            st.success("✅ OpenRouter API key configured")
            st.info("Using DeepSeek model via OpenRouter")
        else:
            st.error("❌ OpenRouter API key not found in secrets")
            st.info("Please add 'OPENROUTER_API_KEY' to your secrets.toml file")
        
        # Clear processed data button
        if st.session_state.processed_candidates:
            if st.button("🗑️ Clear All Data", type="secondary"):
                st.session_state.processed_candidates = []
                st.session_state.processing_complete = False
                st.session_state.excel_data = None
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📤 Upload Resume Files")
        uploaded_files = st.file_uploader(
            "Choose PDF or Word files",
            type=['pdf', 'docx', 'doc'],
            accept_multiple_files=True,
            help="Upload one or more PDF or Word resume files for processing"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
            
            # Display uploaded files with file type validation
            with st.expander("📋 Uploaded Files", expanded=True):
                valid_files = []
                for i, file in enumerate(uploaded_files, 1):
                    file_type = validate_file_type(file)
                    if file_type:
                        st.write(f"{i}. {file.name} ({file.size} bytes) - {file_type.upper()}")
                        valid_files.append(file)
                    else:
                        st.error(f"{i}. {file.name} - Invalid file type")
                
                if len(valid_files) != len(uploaded_files):
                    st.warning(f"Only {len(valid_files)} out of {len(uploaded_files)} files are valid")
            
            # Process files button
            process_disabled = not (credentials_status['gcp_status'] and credentials_status['ai_status']) or st.session_state.processing_in_progress
            
            if st.button("🚀 Process Resumes", type="primary", use_container_width=True, disabled=process_disabled):
                if not credentials_status['gcp_status'] or not credentials_status['ai_status']:
                    st.error("❌ Please configure both Google Cloud Vision and OpenRouter API credentials before processing.")
                else:
                    process_resumes(valid_files)
    
    with col2:
        st.header("📊 Processing Status")
        
        if st.session_state.processing_in_progress:
            st.info("🔄 Processing in progress...")
        elif st.session_state.processed_candidates:
            st.metric("Processed Candidates", len(st.session_state.processed_candidates))
            
            if st.session_state.processing_complete:
                st.success("✅ All resumes processed successfully!")
                
                # Download Excel button
                if st.session_state.excel_data:
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=st.session_state.excel_data,
                        file_name=f"resume_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    if st.button("📥 Generate Excel Report", type="secondary", use_container_width=True):
                        generate_excel_report()
        else:
            st.info("No candidates processed yet. Upload and process resume files to see results here.")
    
    # Display processed candidates
    if st.session_state.processed_candidates:
        st.header("👥 Processed Candidates")
        
        # Create summary table
        display_summary_table()

def validate_file_type(uploaded_file):
    """Validate uploaded file type using file extension"""
    try:
        filename = uploaded_file.name.lower()
        
        # Check file extensions for supported types
        if filename.endswith('.pdf'):
            return 'pdf'
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            return 'word'
        
        return None
        
    except Exception as e:
        st.warning(f"Could not validate file type for {uploaded_file.name}: {str(e)}")
        return None

def check_credentials():
    """Check if all required credentials are available in secrets"""
    ai_status = False
    
    try:

        # Check OpenRouter API key
        if "DEEPSEEK_API_KEY" in st.secrets:
            ai_status = True
            
    except Exception as e:
        st.error(f"Error checking credentials: {str(e)}")
    
    return {
        'ai_status': ai_status
    }

def process_resumes(uploaded_files):
    """Process uploaded resume files"""
    if not uploaded_files:
        st.warning("No valid files to process")
        return
    
    st.session_state.processing_in_progress = True
    st.session_state.processing_complete = False
    st.session_state.processed_candidates = []
    st.session_state.excel_data = None
    
    try:
        # Initialize services
        with st.spinner("Initializing services..."):
            try:
                pdf_processor = PDFProcessor()
                word_processor = WordProcessor()
                text_preprocessor = TextPreprocessor()
                
                # Initialize AIParser with OpenRouter
                ai_parser = AIParser(st.secrets["DEEPSEEK_API_KEY"])
                data_extractor = DataExtractor()
                
            except Exception as e:
                st.error(f"❌ Error initializing services: {str(e)}")
                st.session_state.processing_in_progress = False
                return
        
        # Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
        
        total_files = len(uploaded_files)
        successful_processes = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                current_progress = (i / total_files)
                progress_bar.progress(current_progress)
                status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{total_files})")
                
                # Determine file type and extract text from ALL pages
                file_type = validate_file_type(uploaded_file)
                pages_text = []
                
                if file_type == 'pdf':
                    # Process PDF file - extract text from ALL pages first
                    with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                        pdf_bytes = uploaded_file.read()
                        uploaded_file.seek(0)
                        doc = fitz.open(stream=pdf_bytes, filetype = "pdf")
                        pages_text = []
                        for page_num, page in  enumerate(doc, start=1):
                            try:
                                text = page.get_text()
                                if text.strip():
                                    pages_text.append(text)
                                else:
                                    st.warning(f"No text found of {uploaded_file.name}")
                            except Exception as e: 
                                st.warning(f"Error extracting of {uploaded_file.name}: {str(e)}")

                    
                    
                    # Concatenate all pages and preprocess
                    if pages_text:
                        extracted_text = text_preprocessor.concatenate_pages_text(pages_text)
                    else:
                        extracted_text = ""
                
                elif file_type == 'word':
                    # Process Word file - already contains all pages
                    with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                        raw_text = word_processor.extract_text(uploaded_file)
                        # Normalize the text for better AI parsing
                        extracted_text = text_preprocessor.normalize_text(raw_text)
                
                else:
                    with results_container:
                        st.error(f"❌ Unsupported file type for {uploaded_file.name}")
                    continue
                
                if not extracted_text.strip():
                    with results_container:
                        st.warning(f"⚠️ No text could be extracted from {uploaded_file.name}")
                    continue
                
                # Parse resume using AI
                with st.spinner(f"Analyzing {uploaded_file.name} with AI..."):
                    parsed_data = ai_parser.parse_resume(extracted_text)
                
                # Extract structured data
                with st.spinner(f"Structuring data for {uploaded_file.name}..."):
                    candidate_data = data_extractor.extract_candidate_info(
                        raw_text=extracted_text,
                        ai_parsed_data=parsed_data,
                        filename=uploaded_file.name
                    )
                
                st.session_state.processed_candidates.append(candidate_data)
                successful_processes += 1
                
                # Update progress
                progress_bar.progress((i + 1) / total_files)
                
            except Exception as e:
                with results_container:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
                continue
        
        # Final status update
        progress_bar.progress(1.0)
        status_text.text(f"Processing  {successful_processes}/{total_files} files")
        
        st.session_state.processing_complete = True
        st.session_state.processing_in_progress = False
        
        # Auto-generate Excel if any candidates were processed
        if st.session_state.processed_candidates:
            st.balloons()
            generate_excel_report()
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Critical error during processing: {str(e)}")
        st.session_state.processing_in_progress = False
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

def generate_excel_report():
    """Generate Excel report from processed candidates"""
    try:
        if not st.session_state.processed_candidates:
            st.warning("No candidate data to export")
            return
        
        with st.spinner("Generating Excel report..."):
            exporter = ExcelExporter()
            excel_data = exporter.export_candidates(st.session_state.processed_candidates)
            st.session_state.excel_data = excel_data
            st.success("✅ Excel report generated successfully!")
            
    except Exception as e:
        st.error(f"❌ Error generating Excel report: {str(e)}")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()




