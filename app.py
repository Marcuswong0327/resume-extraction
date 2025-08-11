import streamlit as st
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from resume_parser import ResumeParser
import tempfile
import zipfile
from io import BytesIO

def main():
    st.title("🚀 Bulk Resume Parser")
    st.markdown("Upload multiple resumes (PDF, DOC, DOCX) to extract structured information using pattern recognition")
    
    # Initialize the resume parser
    @st.cache_resource
    def load_parser():
        return ResumeParser
    parser = load_parser()
    
    # File upload section
    st.header("📁 Upload Resumes")
    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'doc', 'docx'],
        accept_multiple_files=True,
        help="Upload PDF, DOC, or DOCX files. Recommended: 50+ files for bulk processing"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
        
        # Display file information
        with st.expander("📋 File Details"):
            file_info = []
            for file in uploaded_files:
                file_info.append({
                    "Filename": file.name,
                    "Size (KB)": round(file.size / 1024, 2),
                    "Type": file.type
                })
            st.dataframe(pd.DataFrame(file_info))
        
        # Processing section
        if st.button("🔄 Process All Resumes", type="primary"):
            process_resumes(uploaded_files, parser)

def process_resumes(uploaded_files, parser):
    """Process all uploaded resumes and generate Excel output"""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Save uploaded files to temporary directory
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    
    status_text.text("💾 Saving uploaded files...")
    for i, uploaded_file in enumerate(uploaded_files):
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append(file_path)
        progress_bar.progress((i + 1) / len(uploaded_files) * 0.2)
    
    # Process files in parallel
    status_text.text("🤖 Processing resumes with AI model...")
    start_time = time.time()
    
    results = []
    processed_count = 0
    
    # Use ThreadPoolExecutor for parallel processing
    max_workers = min(8, len(file_paths))  # Limit to 8 threads for optimal performance
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(parser.parse_resume, file_path): file_path 
            for file_path in file_paths
        }
        
        # Process completed tasks
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                result['filename'] = os.path.basename(file_path)
                results.append(result)
                processed_count += 1
                
                # Update progress
                progress = 0.2 + (processed_count / len(file_paths)) * 0.7
                progress_bar.progress(progress)
                status_text.text(f"🤖 Processed {processed_count}/{len(file_paths)} resumes...")
                
            except Exception as e:
                st.error(f"❌ Error processing {os.path.basename(file_path)}: {str(e)}")
                # Add empty result for failed files
                results.append({
                    'filename': os.path.basename(file_path),
                    'first_name': '',
                    'last_name': '',
                    'phone_number': '',
                    'email_address': '',
                    'current_job_title': '',
                    'current_company': '',
                    'previous_job_titles': '',
                    'previous_companies': ''
                })
                processed_count += 1
    
    processing_time = time.time() - start_time
    
    # Generate Excel file
    status_text.text("📊 Generating Excel file...")
    progress_bar.progress(0.9)
    
    try:
        excel_data = create_excel_output(results)
        progress_bar.progress(1.0)
        
        # Display results
        st.success(f"✅ Processing completed in {processing_time:.2f} seconds!")
        
        # Show summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            st.metric("Successfully Processed", len([r for r in results if r.get('first_name') or r.get('email_address')]))
        with col3:
            st.metric("Processing Time", f"{processing_time:.1f}s")
        with col4:
            st.metric("Speed", f"{len(uploaded_files)/processing_time:.1f} files/sec")
        
        # Display preview of extracted data
        st.header("📊 Extracted Data Preview")
        df = pd.DataFrame(results)
        # Reorder columns for better display
        column_order = ['filename', 'first_name', 'last_name', 'phone_number', 'email_address', 
                       'current_job_title', 'current_company', 'previous_job_titles', 'previous_companies']
        df = df.reindex(columns=[col for col in column_order if col in df.columns])
        st.dataframe(df)
        
        # Download button
        st.download_button(
            label="📥 Download Excel File",
            data=excel_data,
            file_name=f"parsed_resumes_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"❌ Error generating Excel file: {str(e)}")
    finally:
        # Clean up temporary files
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def create_excel_output(results):
    """Create Excel file from parsed results"""
    
    # Prepare data for Excel
    excel_data = []
    for result in results:
        excel_data.append({
            'First Name': result.get('first_name', ''),
            'Last Name': result.get('last_name', ''),
            'Phone Number': result.get('phone_number', ''),
            'Email Address': result.get('email_address', ''),
            'Current Job Title': result.get('current_job_title', ''),
            'Current Company': result.get('current_company', ''),
            'Previous Job Titles': result.get('previous_job_titles', ''),
            'Previous Companies': result.get('previous_companies', '')
        })
    
    # Create DataFrame and Excel file
    df = pd.DataFrame(excel_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Parsed Resumes', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Parsed Resumes']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output.getvalue()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Bulk Resume Parser",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    main()





