import pandas as pd
import io
from typing import List, Dict, Any
import streamlit as st
from datetime import datetime

class SimpleExcelExporter:
    """Handles exporting simplified candidate data to Excel format"""
    
    def __init__(self):
        pass
    
    def export_candidates(self, candidates_data: List[Dict[str, Any]]) -> bytes:
        """
        Export candidates data to Excel file
        
        Args:
            candidates_data: List of candidate information dictionaries
            
        Returns:
            Excel file as bytes
        """
        try:
            if not candidates_data:
                raise ValueError("No candidate data to export")
            
            # Prepare data for DataFrame
            excel_data = []
            
            for candidate in candidates_data:
                row = {
                    'First Name': candidate.get('first_name', ''),
                    'Last Name': candidate.get('last_name', ''),
                    'Mobile': candidate.get('mobile', ''),
                    'Email': candidate.get('email', ''),
                    'Current Job Title': candidate.get('current_job_title', ''),
                    'Current Company': candidate.get('current_company', ''),
                    'Previous Job Title': candidate.get('previous_job_title', ''),
                    'Previous Company': candidate.get('previous_company', ''),
                    'Source File': candidate.get('filename', '')
                }
                excel_data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(excel_data)
            
            # Create Excel writer object
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Write main data sheet
                df.to_excel(writer, sheet_name='Resume Data', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Resume Data']
                
                # Format headers
                for cell in worksheet[1]:
                    cell.font = workbook.create_named_style("header_font").font
                    cell.font.bold = True
                    cell.fill = workbook.create_named_style("header_fill").fill
                    cell.fill.start_color = "CCCCCC"
                    cell.fill.end_color = "CCCCCC"
                    cell.fill.fill_type = "solid"
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    # Set width with some padding, but cap at reasonable maximum
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
            raise e
