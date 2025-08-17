import streamlit as st
import pandas as pd
import json
import traceback
from pdf_processor import PDFProcessor
from word_processor import WordProcessor
from ai_parser import AIParser
from excel_exporter import ExcelExporter
from debug_logger import DebugLogger
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import logging


def main():
    st.set_page_config(page_title="Resume Parser & Analyzer",
                       page_icon="📄",
                       layout="wide")

    st.title("📄 Enhanced Resume Parser & Analyzer")
    st.markdown("Road to Million Biller!!! 🚀")

    # Initialize session state
    if 'processed_candidates' not in st.session_state:
        st.session_state.processed_candidates = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'processing_in_progress' not in st.session_state:
        st.session_state.processing_in_progress = False
    if 'debug_logger' not in st.session_state:
        st.session_state.debug_logger = DebugLogger()

    # Debug mode toggle
    col_debug1, col_debug2 = st.columns([3, 1])
    with col_debug2:
        if st.button("🐛 Toggle Debug Mode"):
            if st.session_state.debug_logger.debug_mode:
                st.session_state.debug_logger.disable_debug_mode()
            else:
                st.session_state.debug_logger.enable_debug_mode()
                os.environ["DEBUG_MODE"] = "true"

    # Check credentials availability
    credentials_status = check_credentials()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📤 Upload Resume Files")
        uploaded_files = st.file_uploader(
            "Upload up to 100 files (PDF, DOCX supported)",
            type=['pdf', 'docx', 'doc'],
            accept_multiple_files=True,
        )

        if uploaded_files:
            st.success(
                f"✅ {len(uploaded_files)} file(s) uploaded successfully")

            # Validate file types and sizes
            valid_files, invalid_files = validate_uploaded_files(
                uploaded_files)

            if invalid_files:
                st.warning(f"⚠️ {len(invalid_files)} files have issues:")
                for file_issue in invalid_files:
                    st.text(f"• {file_issue}")

            if valid_files:
                st.info(
                    f"✅ {len(valid_files)} valid files ready for processing")

                # Display uploaded files
                with st.expander("📋 Valid Files", expanded=False):
                    for i, file in enumerate(valid_files, 1):
                        file_type = file.name.split('.')[-1].upper()
                        file_size_mb = file.size / (1024 * 1024)
                        st.write(
                            f"{i}. {file.name} ({file_size_mb:.2f} MB) - {file_type}"
                        )

                # Process files button
                process_disabled = not credentials_status[
                    'deepseek_status'] or st.session_state.processing_in_progress

                if st.button("🚀 Process Resumes",
                             type="primary",
                             use_container_width=True,
                             disabled=process_disabled):
                    if not credentials_status['deepseek_status']:
                        st.error(
                            "❌ Please configure OpenRouter API credentials before processing."
                        )
                    else:
                        process_resumes(valid_files)

    with col2:
        st.header("📊 Processing Status")

        # Show debug mode status
        debug_status = "🐛 ON" if st.session_state.debug_logger.debug_mode else "OFF"
        st.info(f"Debug Mode: {debug_status}")

        if st.session_state.processing_in_progress:
            st.info("🔄 Processing in progress...")
        elif st.session_state.processed_candidates:
            st.metric("Processed Candidates",
                      len(st.session_state.processed_candidates))

            # Show completion stats
            successful_extractions = len([
                c for c in st.session_state.processed_candidates if any([
                    c.get('first_name'),
                    c.get('email'),
                    c.get('current_job_title')
                ])
            ])
            st.metric("Successful Extractions", successful_extractions)

            if st.session_state.processing_complete:
                st.success("✅ Processing completed!")

                if st.button("📊 Download Excel Report",
                             type="secondary",
                             use_container_width=True):
                    generate_and_download_excel()
        else:
            st.info("No candidates processed yet.")

    # Display processed candidates
    if st.session_state.processed_candidates:
        st.header("👥 Processed Candidates")

        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            show_only_successful = st.checkbox(
                "Show only successful extractions", value=False)
        with col_filter2:
            show_empty_fields = st.checkbox("Show empty fields", value=True)

        # Create DataFrame for display
        display_data = []
        for i, candidate in enumerate(st.session_state.processed_candidates,
                                      1):
            # Check if extraction was successful
            has_data = any([
                candidate.get('first_name'),
                candidate.get('email'),
                candidate.get('current_job_title')
            ])

            if show_only_successful and not has_data:
                continue

            row_data = {
                'Sr.': i,
                'First Name': candidate.get('first_name', ''),
                'Last Name': candidate.get('last_name', ''),
                'Mobile': candidate.get('mobile', ''),
                'Email': candidate.get('email', ''),
                'Current Job Title': candidate.get('current_job_title', ''),
                'Current Company': candidate.get('current_company', ''),
                'Previous Job Title': candidate.get('previous_job_title', ''),
                'Previous Company': candidate.get('previous_company', ''),
                'Source File': candidate.get('filename', ''),
                'Status': '✅ Success' if has_data else '❌ Failed'
            }

            if not show_empty_fields:
                # Remove empty fields from display
                row_data = {
                    k: v
                    for k, v in row_data.items()
                    if v or k in ['Sr.', 'Source File', 'Status']
                }

            display_data.append(row_data)

        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data to display with current filters.")


def validate_uploaded_files(uploaded_files):
    """Validate uploaded files for type and size"""
    valid_files = []
    invalid_files = []

    for file in uploaded_files:
        issues = []

        # Check file extension
        file_ext = file.name.lower().split('.')[-1]
        if file_ext not in ['pdf', 'docx', 'doc']:
            issues.append(f"{file.name}: Unsupported format ({file_ext})")

        # Check file size (50MB for PDF, 10MB for Word)
        max_size = 50 * 1024 * 1024 if file_ext == 'pdf' else 10 * 1024 * 1024
        if file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            issues.append(
                f"{file.name}: Too large ({file.size / (1024 * 1024):.1f}MB > {max_size_mb}MB)"
            )

        # Check if file is empty
        if file.size == 0:
            issues.append(f"{file.name}: Empty file")

        if issues:
            invalid_files.extend(issues)
        else:
            valid_files.append(file)

    return valid_files, invalid_files


def check_credentials():
    """Check API credentials availability"""
    deepseek_status = False

    try:
        # Check OpenRouter API key
        api_key = os.getenv("DEEPSEEK_API_KEY") or st.secrets.get(
            "DEEPSEEK_API_KEY")
        if api_key:
            deepseek_status = True
        else:
            st.error("❌ DEEPSEEK_API_KEY not found in environment or secrets")

    except Exception as e:
        st.error(f"❌ Error checking credentials: {str(e)}")

    return {'deepseek_status': deepseek_status}


def process_resumes(uploaded_files):
    """Enhanced resume processing with comprehensive debugging"""
    st.session_state.processing_in_progress = True
    st.session_state.processing_complete = False
    st.session_state.processed_candidates = []

    debug_logger = st.session_state.debug_logger

    try:
        # Initialize services
        with st.spinner("🔧 Initializing services..."):
            try:
                pdf_processor = PDFProcessor()
                word_processor = WordProcessor()

                # Get API key from environment or secrets
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    try:
                        api_key = st.secrets["DEEPSEEK_API_KEY"]
                    except:
                        api_key = None
                
                if not api_key:
                    raise Exception("DEEPSEEK_API_KEY not found in environment variables or secrets")
                    
                ai_parser = AIParser(api_key)

                st.success("✅ Services initialized successfully")

            except Exception as e:
                debug_logger.log_error("Service Initialization", "System", e)
                st.session_state.processing_in_progress = False
                return

        # Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            error_summary = st.empty()

        total_files = len(uploaded_files)
        successful_processes = 0
        extraction_failures = 0
        parsing_failures = 0

        def process_single_file(uploaded_file):
            """Process a single file with comprehensive error tracking"""
            filename = uploaded_file.name
            file_extension = filename.lower().split('.')[-1]
            extracted_text = ""

            try:
                # Text extraction phase
                if file_extension == 'pdf':
                    extracted_text = pdf_processor.process_pdf_file(
                        uploaded_file)
                elif file_extension in ['doc', 'docx']:
                    extracted_text = word_processor.process_word_file(
                        uploaded_file)
                else:
                    debug_logger.log_error(
                        "File Processing", filename,
                        f"Unsupported file type: {file_extension}")
                    return None

                # Validate extracted text
                if not debug_logger.validate_extracted_text(
                        extracted_text, filename):
                    return {
                        'filename': filename,
                        'extraction_error': True,
                        **ai_parser._create_empty_structure()
                    }

                debug_logger.log_text_extraction(filename, extracted_text,
                                                 file_extension.upper())

                # AI parsing phase
                parsed_data = ai_parser.parse_resume(extracted_text, filename)
                parsed_data['filename'] = filename

                debug_logger.log_ai_parsing(filename, len(extracted_text),
                                            "Success", parsed_data)

                return parsed_data

            except Exception as e:
                debug_logger.log_error("File Processing", filename, e)
                return {
                    'filename': filename,
                    'processing_error': True,
                    **ai_parser._create_empty_structure()
                }

        # Process files with optimized batching for speed and reliability
        results = []

        # Use maximum parallelism for 16-core systems
        batch_size = 4 
        max_workers = 8  
        
        # Process in batches
        for batch_start in range(0, len(uploaded_files), batch_size):
            batch_end = min(batch_start + batch_size, len(uploaded_files))
            batch_files = uploaded_files[batch_start:batch_end]
            
            # Process current batch in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(process_single_file, f): f 
                    for f in batch_files
                }
                
                for future in as_completed(future_to_file):
                    uploaded_file = future_to_file[future]
                    
                    try:
                        result = future.result(timeout=90)  # 90 second timeout per file
                        
                        if result:
                            results.append(result)
                            
                            # Check if extraction was successful
                            if result.get('extraction_error'):
                                extraction_failures += 1
                            elif not any([
                                    result.get('first_name'),
                                    result.get('email'),
                                    result.get('current_job_title')
                            ]):
                                parsing_failures += 1
                            else:
                                successful_processes += 1
                                
                    except Exception as e:
                        debug_logger.log_error("File Processing", uploaded_file.name, e)
                        extraction_failures += 1
                        # Create empty result for failed file
                        results.append({
                            'filename': uploaded_file.name,
                            'processing_error': True,
                            **ai_parser._create_empty_structure()
                        })

                    # Update progress
                    progress = len(results) / total_files
                    progress_bar.progress(progress)
                    status_text.text(f"Processed {len(results)} / {total_files} resumes")

                    # Update error summary
                    error_summary.info(
                        f"✅ Successful: {successful_processes} | "
                        f"⚠️ Extraction Failed: {extraction_failures} | "
                        f"🤖 Parsing Failed: {parsing_failures}")
            
            # Minimal delay between batches for maximum speed
            if batch_end < len(uploaded_files):
                import time
                time.sleep(0.1)  # 100ms delay between batches

        # Store results
        st.session_state.processed_candidates = results

        # Final progress update
        progress_bar.progress(1.0)
        status_text.text(
            f"Processing complete: {len(results)} files processed")
        st.session_state.processing_complete = True
        st.session_state.processing_in_progress = False

        # Show final summary
        if successful_processes > 0:
            st.success(
                f"🎉 Successfully processed {successful_processes}/{total_files} resume files."
            )

        if extraction_failures > 0:
            st.warning(
                f"⚠️ {extraction_failures} files had text extraction issues.")

        if parsing_failures > 0:
            st.warning(f"🤖 {parsing_failures} files had AI parsing issues.")

        if successful_processes == 0:
            st.error(
                "❌ No files were successfully processed. Please check your files and try again."
            )
            if debug_logger.debug_mode:
                st.info(
                    "💡 Debug mode is enabled. Check the detailed logs above for troubleshooting."
                )

    except Exception as e:
        debug_logger.log_error("System", "Processing Pipeline", e)
        st.session_state.processing_in_progress = False

        with st.expander("🔍 System Error Details"):
            st.code(traceback.format_exc())


def generate_and_download_excel():
    """Generate and auto-download Excel report with enhanced error handling"""
    try:
        if not st.session_state.processed_candidates:
            st.warning("⚠️ No candidate data to export.")
            return

        with st.spinner("📊 Generating Excel report..."):
            exporter = ExcelExporter()
            excel_data = exporter.export_candidates(
                st.session_state.processed_candidates)

            # Create download link
            b64 = base64.b64encode(excel_data).decode()
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_analysis_{timestamp}.xlsx"

            # Use st.download_button for better UX
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_data,
                file_name=filename,
                mime=
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary")

            st.success(f"✅ Excel report generated successfully: {filename}")

    except Exception as e:
        st.error(f"❌ Error generating Excel report: {str(e)}")
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    main()

