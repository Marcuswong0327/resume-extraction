import pandas as pd
import io
from typing import List, Dict, Any
import streamlit as st
from datetime import datetime

class ExcelExporter:
    """Handles exporting candidate data to Excel format"""
    
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
            
            # Create Excel writer object
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Create main summary sheet
                self._create_main_summary_sheet(candidates_data, writer)
                
                # Create detailed sheet with all information
                self._create_detailed_sheet(candidates_data, writer)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
            raise e
    
    def _create_main_summary_sheet(self, candidates_data: List[Dict], writer):
        """
        Create main summary sheet with key candidate information
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        summary_data = []
        
        for i, candidate in enumerate(candidates_data, 1):
            summary_row = {
                'ID': i,
                'First_Name': candidate.get('first_name', ''),
                'Family_Name': candidate.get('family_name', ''),
                'Email': candidate.get('email', ''),
                'Phone': candidate.get('phone', ''),
                'Job_Title': candidate.get('job_title', ''),
                'Source_File': candidate.get('filename', '')
            }
            summary_data.append(summary_row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Candidate_Summary', index=False)
        
        # Auto-adjust column widths
        self._adjust_column_widths(writer.sheets['Candidate_Summary'])
    
    def _create_detailed_sheet(self, candidates_data: List[Dict], writer):
        """
        Create detailed sheet with all extracted information
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        detailed_data = []
        
        for i, candidate in enumerate(candidates_data, 1):
            # Basic information row
            detailed_row = {
                'Candidate_ID': i,
                'Category': 'Personal Info',
                'Field': 'Complete Information',
                'First_Name': candidate.get('first_name', ''),
                'Family_Name': candidate.get('family_name', ''),
                'Email': candidate.get('email', ''),
                'Phone': candidate.get('phone', ''),
                'Job_Title': candidate.get('job_title', ''),
                'Source_File': candidate.get('filename', ''),
                'Processing_Status': 'Success' if any([
                    candidate.get('first_name'),
                    candidate.get('family_name'),
                    candidate.get('email'),
                    candidate.get('phone'),
                    candidate.get('job_title')
                ]) else 'Limited Data'
            }
            detailed_data.append(detailed_row)
        
        detailed_df = pd.DataFrame(detailed_data)
        detailed_df.to_excel(writer, sheet_name='Detailed_Information', index=False)
        
        # Auto-adjust column widths
        self._adjust_column_widths(writer.sheets['Detailed_Information'])
    
    def _adjust_column_widths(self, worksheet):
        """
        Auto-adjust column widths for better readability
        
        Args:
            worksheet: Excel worksheet object
        """
        try:
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        except Exception as e:
            st.warning(f"Could not adjust column widths: {str(e)}")
    
    def create_statistics_summary(self, candidates_data: List[Dict]) -> Dict:
        """
        Create statistics summary of the processing results
        
        Args:
            candidates_data: List of candidate data
            
        Returns:
            Dictionary with processing statistics
        """
        try:
            total_candidates = len(candidates_data)
            
            stats = {
                'total_candidates': total_candidates,
                'with_first_name': sum(1 for c in candidates_data if c.get('first_name', '').strip()),
                'with_family_name': sum(1 for c in candidates_data if c.get('family_name', '').strip()),
                'with_email': sum(1 for c in candidates_data if c.get('email', '').strip()),
                'with_phone': sum(1 for c in candidates_data if c.get('phone', '').strip()),
                'with_job_title': sum(1 for c in candidates_data if c.get('job_title', '').strip()),
                'complete_profiles': 0,
                'partial_profiles': 0,
                'empty_profiles': 0
            }
            
            # Calculate profile completeness
            for candidate in candidates_data:
                fields_filled = sum(1 for field in ['first_name', 'family_name', 'email', 'phone', 'job_title']
                                  if candidate.get(field, '').strip())
                
                if fields_filled >= 4:
                    stats['complete_profiles'] += 1
                elif fields_filled >= 2:
                    stats['partial_profiles'] += 1
                else:
                    stats['empty_profiles'] += 1
            
            # Calculate percentages
            if total_candidates > 0:
                for key in ['with_first_name', 'with_family_name', 'with_email', 'with_phone', 'with_job_title']:
                    percentage_value = (stats[key] / total_candidates) * 100
                    stats[f'{key}_percent'] = round(percentage_value, 1)
            
            return stats
            
        except Exception as e:
            st.error(f"Error creating statistics summary: {str(e)}")
            return {}
