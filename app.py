import streamlit as st
import pandas as pd
import json
import traceback
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
    st.markdown("Upload multiple PDF resumes to extract and analyze candidate information using AI-powered parsing.")
    
    # Initialize session state
    if 'processed_candidates' not in st.session_state:
        st.session_state.processed_candidates = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'processing_in_progress' not in st.session_state:
        st.session_state.processing_in_progress = False
    
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
                st.info("Please add GCP credentials (GCP_TYPE, GCP_PROJECT_ID, GCP_PRIVATE_KEY, GCP_CLIENT_EMAIL, etc.) to your secrets.toml file")
        
        # OpenRouter API Configuration
        st.subheader("OpenRouter (DeepSeek R1 0528)") # Updated title
        if credentials_status['deepseek_status']:
            st.success("✅ OpenRouter API key configured")
            st.info("Using DeepSeek R1 0528 model via OpenRouter") # Updated info
        else:
            st.error("❌ OpenRouter API key not found in secrets")
            st.info("Please add 'DEEPSEEK_API_KEY' (OpenRouter key) to your secrets.toml file")
    
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
            process_disabled = not (credentials_status['gcp_status'] and credentials_status['deepseek_status']) or st.session_state.processing_in_progress
            
            if st.button("🚀 Process Resumes", type="primary", use_container_width=True, disabled=process_disabled):
                st.write("DEBUG: Button clicked!")
                st.write(f"DEBUG: GCP status: {credentials_status['gcp_status']}")
                st.write(f"DEBUG: DeepSeek status: {credentials_status['deepseek_status']}")
                
                if not credentials_status['gcp_status'] or not credentials_status['deepseek_status']:
                    st.error("❌ Please configure both Google Cloud Vision and OpenRouter API credentials before processing.")
                else:
                    st.write("DEBUG: Starting process_resumes function")
                    process_resumes(uploaded_files)
    
    with col2:
        st.header("📊 Processing Status")
        
        if st.session_state.processing_in_progress:
            st.info("🔄 Processing in progress...")
        elif st.session_state.processed_candidates:
            st.metric("Processed Candidates", len(st.session_state.processed_candidates))
            
            if st.session_state.processing_complete:
                st.success("✅ All resumes processed successfully!")
                
                # Auto-generate Excel file
                if st.button("📥 Generate Excel Report", type="secondary", use_container_width=True):
                    generate_and_download_excel()
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

def check_credentials():
    """Check if all required credentials are available in secrets"""
    gcp_status = False
    deepseek_status = False
    
    try:
        # Check GCP credentials using the specific naming convention
        required_gcp_keys = [
            "GCP_TYPE", "GCP_PROJECT_ID", "GCP_PRIVATE_KEY", "GCP_CLIENT_EMAIL"
        ]
        
        if all(key in st.secrets for key in required_gcp_keys):
            gcp_status = True
        
        # Check DeepSeek API key (now OpenRouter key)
        if "DEEPSEEK_API_KEY" in st.secrets:
            deepseek_status = True
            
    except Exception as e:
        st.error(f"Error checking credentials: {str(e)}")
    
    return {
        'gcp_status': gcp_status,
        'deepseek_status': deepseek_status
    }

def process_resumes(uploaded_files):
    """Process uploaded resume files"""
    st.write("DEBUG: process_resumes function started")
    st.write(f"DEBUG: Number of files to process: {len(uploaded_files)}")
    
    st.session_state.processing_in_progress = True
    st.session_state.processing_complete = False
    st.session_state.processed_candidates = []
    
    try:
        st.write("DEBUG: Entering try block")
        # Initialize services with proper error handling
        with st.spinner("Initializing services..."):
            try:
                pdf_processor = PDFProcessor()
                
                # Create GCP credentials dictionary using the correct naming convention
                gcp_credentials = {
                    "type": st.secrets["GCP_TYPE"],
                    "project_id": st.secrets["GCP_PROJECT_ID"],
                    "private_key_id": st.secrets["GCP_PRIVATE_KEY_ID"],
                    "private_key": st.secrets["GCP_PRIVATE_KEY"].replace('\\n', '\n'),
                    "client_email": st.secrets["GCP_CLIENT_EMAIL"],
                    "client_id": st.secrets["GCP_CLIENT_ID"],
                    "auth_uri": st.secrets.get("GCP_AUTH_URI", "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"),
                    "token_uri": st.secrets.get("GCP_TOKEN_URI", "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"),
                    "auth_provider_x509_cert_url": st.secrets.get("GCP_AUTH_PROVIDER_X509_CERT_URL", "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"),
                    "client_x509_cert_url": st.secrets.get("GCP_CLIENT_X509_CERT_URL", ""),
                    "universe_domain": st.secrets.get("GCP_UNIVERSE_DOMAIN", "googleapis.com")
                }
                
                ocr_service = OCRService(gcp_credentials)
                
                # --- MODIFICATION START ---
                openrouter_base_url = "https://openrouter.ai/api/v1/chat/completions"
                openrouter_model_name = "deepseek/deepseek-chat-v3-0324" # Use the specific model name
                
                # Initialize AIParser with OpenRouter base URL and model name
                ai_parser = AIParser(
                    st.secrets["DEEPSEEK_API_KEY"],
                    base_url=openrouter_base_url,
                    model_name=openrouter_model_name
                )
                # --- MODIFICATION END ---
                
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
            error_container = st.container()
        
        total_files = len(uploaded_files)
        successful_processes = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                current_progress = (i / total_files)
                progress_bar.progress(current_progress)
                status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{total_files})")
                
                # Convert PDF to images
                with st.spinner(f"Converting {uploaded_file.name} to images..."):
                    images = pdf_processor.pdf_to_images(uploaded_file)
                
                if not images:
                    with error_container:
                        st.warning(f"⚠️ No images could be extracted from {uploaded_file.name}")
                    continue
                
                # Extract text using OCR
                with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                    extracted_text = ""
                    for page_num, image in enumerate(images):
                        try:
                            text_from_page = ocr_service.extract_text_from_image(image)
                            extracted_text += text_from_page + "\n"
                        except Exception as ocr_error:
                            with error_container:
                                st.warning(f"⚠️ OCR failed for page {page_num + 1} of {uploaded_file.name}: {str(ocr_error)}")
                
                if not extracted_text.strip():
                    with error_container:
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
                
                # Show success for current file
                with error_container:
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                
            except Exception as e:
                with error_container:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
                continue
        
        # Final status update
        progress_bar.progress(1.0)
        status_text.text(f"✅ Processing complete! Successfully processed {successful_processes}/{total_files} files")
        
        st.session_state.processing_complete = True
        st.session_state.processing_in_progress = False
        
        # Auto-generate Excel if any candidates were processed
        if st.session_state.processed_candidates:
            st.balloons()
            with st.spinner("Generating Excel report..."):
                generate_and_download_excel()
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ An unexpected error occurred during processing: {str(e)}")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        st.session_state.processing_in_progress = False

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
                
                if candidate.get('summary'):
                    st.subheader("📝 Summary")
                    st.write(candidate['summary'])
                
                st.subheader("🎓 Education")
                education = candidate.get('education_formatted', candidate.get('education', []))
                if education:
                    for edu in education:
                        st.write(f"• {edu}")
                else:
                    st.write("No education information found")
            
            with col2:
                st.subheader("💼 Work Experience")
                experience = candidate.get('experience_formatted', candidate.get('experience', []))
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

def generate_and_download_excel():
    """Generate and provide download for Excel file"""
    try:
        with st.spinner("Generating Excel file..."):
            exporter = ExcelExporter()
            excel_file = exporter.export_candidates(st.session_state.processed_candidates)
            
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f"resume_analysis_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_file,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success("✅ Excel file generated successfully! Click the download button above.")
        
    except Exception as e:
        st.error(f"❌ Error generating Excel file: {str(e)}")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()


