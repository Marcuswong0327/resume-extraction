import streamlit as st
import pandas as pd
import os
import json
from utils.pdf_processor import PDFProcessor
from utils.ocr_service import OCRService
from utils.ai_parser import AIParser
from utils.data_extractor import DataExtractor
from utils.excel_exporter import ExcelExporter

def main():
    st.set_page_config(
        page_title="Resume Parser & Analyzer",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume Parser & Analyzer")
    st.markdown("Upload multiple PDF resumes to extract and analyze candidate information using AI-powered parsing.")
    
    # Initialize session state
    if 'processed_candidates' not in st.session_state:
        st.session_state.processed_candidates = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Google Cloud Vision API Configuration
        st.subheader("Google Cloud Vision API")
        with st.expander("API Credentials", expanded=False):
            st.info("Ensure your Google Cloud Vision API credentials are set up in environment variables or provide them here.")
            
            # Check if credentials are available
            gcp_credentials = {
                "type": os.getenv("GCP_TYPE", "service_account"),
                "project_id": os.getenv("GCP_PROJECT_ID", ""),
                "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID", ""),
                "private_key": os.getenv("GCP_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("GCP_CLIENT_EMAIL", ""),
                "client_id": os.getenv("GCP_CLIENT_ID", ""),
                "auth_uri": os.getenv("GCP_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("GCP_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL", ""),
                "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN", "googleapis.com")
            }
            
            if gcp_credentials["project_id"]:
                st.success(f"✅ Project ID: {gcp_credentials['project_id']}")
            else:
                st.error("❌ Google Cloud credentials not found in environment variables")
        
        # DeepSeek API Configuration
        st.subheader("DeepSeek V3 API")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_api_key:
            st.success("✅ DeepSeek API key configured")
        else:
            st.error("❌ DeepSeek API key not found in environment variables")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📤 Upload Resume Files")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF resume files for processing"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
            
            # Display uploaded files
            with st.expander("📋 Uploaded Files", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size} bytes)")
            
            # Process files button
            if st.button("🚀 Process Resumes", type="primary", use_container_width=True):
                if not gcp_credentials["project_id"] or not deepseek_api_key:
                    st.error("❌ Please configure both Google Cloud Vision and DeepSeek API credentials before processing.")
                else:
                    process_resumes(uploaded_files, gcp_credentials, deepseek_api_key)
    
    with col2:
        st.header("📊 Processing Status")
        if st.session_state.processed_candidates:
            st.metric("Processed Candidates", len(st.session_state.processed_candidates))
            
            if st.session_state.processing_complete:
                st.success("✅ All resumes processed successfully!")
                
                # Export to Excel button
                if st.button("📥 Export to Excel", type="secondary", use_container_width=True):
                    export_to_excel()
        else:
            st.info("No candidates processed yet. Upload and process resume files to see results here.")
    
    # Display processed candidates
    if st.session_state.processed_candidates:
        st.header("👥 Processed Candidates")
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["📋 Summary View", "📄 Detailed View"])
        
        with tab1:
            display_summary_view()
        
        with tab2:
            display_detailed_view()

def process_resumes(uploaded_files, gcp_credentials, deepseek_api_key):
    """Process uploaded resume files"""
    try:
        # Initialize services
        pdf_processor = PDFProcessor()
        ocr_service = OCRService(gcp_credentials)
        ai_parser = AIParser(deepseek_api_key)
        data_extractor = DataExtractor()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.session_state.processed_candidates = []
        total_files = len(uploaded_files)
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{total_files})")
                
                # Convert PDF to images
                images = pdf_processor.pdf_to_images(uploaded_file)
                
                # Extract text using OCR
                extracted_text = ""
                for image in images:
                    text_from_page = ocr_service.extract_text_from_image(image)
                    extracted_text += text_from_page + "\n"
                
                if not extracted_text.strip():
                    st.warning(f"⚠️ No text could be extracted from {uploaded_file.name}")
                    continue
                
                # Parse resume using AI
                parsed_data = ai_parser.parse_resume(extracted_text)
                
                # Extract structured data
                candidate_data = data_extractor.extract_candidate_info(
                    raw_text=extracted_text,
                    ai_parsed_data=parsed_data,
                    filename=uploaded_file.name
                )
                
                st.session_state.processed_candidates.append(candidate_data)
                
                # Update progress
                progress_bar.progress((i + 1) / total_files)
                
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                continue
        
        status_text.text("✅ Processing complete!")
        st.session_state.processing_complete = True
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ An error occurred during processing: {str(e)}")

def display_summary_view():
    """Display summary view of processed candidates"""
    if not st.session_state.processed_candidates:
        return
    
    # Create summary dataframe
    summary_data = []
    for candidate in st.session_state.processed_candidates:
        summary_data.append({
            "Name": candidate.get("name", "N/A"),
            "Email": candidate.get("email", "N/A"),
            "Phone": candidate.get("phone", "N/A"),
            "Skills Count": len(candidate.get("skills", [])),
            "Experience Count": len(candidate.get("experience", [])),
            "Education Count": len(candidate.get("education", [])),
            "Source File": candidate.get("filename", "N/A")
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True)

def display_detailed_view():
    """Display detailed view of processed candidates"""
    if not st.session_state.processed_candidates:
        return
    
    for i, candidate in enumerate(st.session_state.processed_candidates):
        with st.expander(f"👤 {candidate.get('name', f'Candidate {i+1}')}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Basic Information")
                st.write(f"**Name:** {candidate.get('name', 'N/A')}")
                st.write(f"**Email:** {candidate.get('email', 'N/A')}")
                st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                st.write(f"**Source File:** {candidate.get('filename', 'N/A')}")
                
                st.subheader("🎓 Education")
                education = candidate.get('education', [])
                if education:
                    for edu in education:
                        st.write(f"• {edu}")
                else:
                    st.write("No education information found")
            
            with col2:
                st.subheader("💼 Work Experience")
                experience = candidate.get('experience', [])
                if experience:
                    for exp in experience:
                        st.write(f"• {exp}")
                else:
                    st.write("No work experience found")
                
                st.subheader("🛠️ Skills")
                skills = candidate.get('skills', [])
                if skills:
                    skills_text = ", ".join(skills)
                    st.write(skills_text)
                else:
                    st.write("No skills found")

def export_to_excel():
    """Export processed candidates to Excel file"""
    try:
        exporter = ExcelExporter()
        excel_file = exporter.export_candidates(st.session_state.processed_candidates)
        
        st.download_button(
            label="📥 Download Excel File",
            data=excel_file,
            file_name=f"resume_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.success("✅ Excel file generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error generating Excel file: {str(e)}")

if __name__ == "__main__":
    main()
