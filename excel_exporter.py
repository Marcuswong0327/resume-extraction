import pandas as pd
import io
from typing import List, Dict, Any
import streamlit as st

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
            # Create Excel writer object
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Create summary sheet
                self._create_summary_sheet(candidates_data, writer)
                
                # Create detailed sheets for each candidate
                self._create_detailed_sheets(candidates_data, writer)
                
                # Create skills analysis sheet
                self._create_skills_analysis_sheet(candidates_data, writer)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
            raise e
    
    def _create_summary_sheet(self, candidates_data: List[Dict], writer):
        """
        Create summary sheet with overview of all candidates
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        summary_data = []
        
        for i, candidate in enumerate(candidates_data, 1):
            summary_row = {
                'Candidate_ID': i,
                'Name': candidate.get('name', 'N/A'),
                'Email': candidate.get('email', 'N/A'),
                'Phone': candidate.get('phone', 'N/A'),
                'Total_Skills': len(candidate.get('skills', [])),
                'Work_Experience_Count': len(candidate.get('experience', [])),
                'Education_Count': len(candidate.get('education', [])),
                'Top_Skills': ', '.join(candidate.get('skills', [])[:5]),  # Top 5 skills
                'Source_File': candidate.get('filename', 'N/A')
            }
            summary_data.append(summary_row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Summary']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _create_detailed_sheets(self, candidates_data: List[Dict], writer):
        """
        Create detailed sheets for each candidate
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        for i, candidate in enumerate(candidates_data, 1):
            try:
                sheet_name = f"Candidate_{i}"
                if len(sheet_name) > 31:  # Excel sheet name limit
                    sheet_name = f"Candidate_{i}"[:31]
                
                # Prepare detailed data
                detailed_data = {
                    'Field': [],
                    'Value': []
                }
                
                # Basic information
                detailed_data['Field'].extend([
                    'Name', 'Email', 'Phone', 'Source File', 'Summary'
                ])
                detailed_data['Value'].extend([
                    candidate.get('name', 'N/A'),
                    candidate.get('email', 'N/A'),
                    candidate.get('phone', 'N/A'),
                    candidate.get('filename', 'N/A'),
                    candidate.get('summary', 'N/A')
                ])
                
                # Skills
                skills = candidate.get('skills', [])
                if skills:
                    detailed_data['Field'].append('Skills')
                    detailed_data['Value'].append('; '.join(skills))
                
                # Work Experience
                experience = candidate.get('experience_formatted', candidate.get('experience', []))
                if experience:
                    for j, exp in enumerate(experience, 1):
                        detailed_data['Field'].append(f'Work Experience {j}')
                        if isinstance(exp, dict):
                            exp_text = f"{exp.get('position', '')} at {exp.get('company', '')} ({exp.get('duration', '')})"
                            if exp.get('description'):
                                exp_text += f" - {exp.get('description')}"
                            detailed_data['Value'].append(exp_text)
                        else:
                            detailed_data['Value'].append(str(exp))
                
                # Education
                education = candidate.get('education_formatted', candidate.get('education', []))
                if education:
                    for j, edu in enumerate(education, 1):
                        detailed_data['Field'].append(f'Education {j}')
                        if isinstance(edu, dict):
                            edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')} ({edu.get('year', '')})"
                            detailed_data['Value'].append(edu_text)
                        else:
                            detailed_data['Value'].append(str(edu))
                
                # Create DataFrame and export
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 80)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                    
            except Exception as e:
                st.warning(f"Error creating detailed sheet for candidate {i}: {str(e)}")
                continue
    
    def _create_skills_analysis_sheet(self, candidates_data: List[Dict], writer):
        """
        Create skills analysis sheet with aggregated skills data
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        try:
            # Aggregate all skills
            skills_count = {}
            candidate_skills = {}
            
            for i, candidate in enumerate(candidates_data, 1):
                candidate_name = candidate.get('name', f'Candidate {i}')
                skills = candidate.get('skills', [])
                
                candidate_skills[candidate_name] = skills
                
                for skill in skills:
                    if skill in skills_count:
                        skills_count[skill] += 1
                    else:
                        skills_count[skill] = 1
            
            # Create skills frequency data
            skills_frequency_data = []
            for skill, count in sorted(skills_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(candidates_data)) * 100
                skills_frequency_data.append({
                    'Skill': skill,
                    'Candidates_Count': count,
                    'Percentage': f"{percentage:.1f}%"
                })
            
            skills_df = pd.DataFrame(skills_frequency_data)
            skills_df.to_excel(writer, sheet_name='Skills_Analysis', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Skills_Analysis']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 40)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
        except Exception as e:
            st.warning(f"Error creating skills analysis sheet: {str(e)}")
    
    def create_candidate_comparison_report(self, candidates_data: List[Dict]) -> pd.DataFrame:
        """
        Create a comparison report DataFrame for candidates
        
        Args:
            candidates_data: List of candidate data
            
        Returns:
            DataFrame with comparison data
        """
        try:
            comparison_data = []
            
            for i, candidate in enumerate(candidates_data, 1):
                skills = candidate.get('skills', [])
                experience = candidate.get('experience', [])
                education = candidate.get('education', [])
                
                comparison_row = {
                    'Candidate_ID': i,
                    'Name': candidate.get('name', 'N/A'),
                    'Email': candidate.get('email', 'N/A'),
                    'Phone': candidate.get('phone', 'N/A'),
                    'Total_Skills': len(skills),
                    'Programming_Skills': len([s for s in skills if any(tech in s.lower() for tech in ['python', 'java', 'javascript', 'c++', 'c#'])]),
                    'Years_Experience': self._estimate_experience_years(experience),
                    'Education_Level': self._get_highest_education_level(education),
                    'Has_Contact_Info': 'Yes' if candidate.get('email') or candidate.get('phone') else 'No',
                    'Source_File': candidate.get('filename', 'N/A')
                }
                comparison_data.append(comparison_row)
            
            return pd.DataFrame(comparison_data)
            
        except Exception as e:
            st.error(f"Error creating comparison report: {str(e)}")
            return pd.DataFrame()
    
    def _estimate_experience_years(self, experience_list: List) -> str:
        """
        Estimate years of experience from experience entries
        
        Args:
            experience_list: List of experience entries
            
        Returns:
            Estimated experience as string
        """
        if not experience_list:
            return "N/A"
        
        # Simple heuristic: assume each job is 2-3 years average
        estimated_years = len(experience_list) * 2.5
        return f"~{estimated_years:.0f} years"
    
    def _get_highest_education_level(self, education_list: List) -> str:
        """
        Determine highest education level
        
        Args:
            education_list: List of education entries
            
        Returns:
            Highest education level as string
        """
        if not education_list:
            return "N/A"
        
        education_levels = {
            'phd': 5, 'doctorate': 5, 'ph.d': 5,
            'master': 4, "master's": 4, 'mba': 4, 'ms': 4, 'ma': 4,
            'bachelor': 3, "bachelor's": 3, 'bs': 3, 'ba': 3, 'bsc': 3,
            'associate': 2, 'diploma': 1, 'certificate': 1
        }
        
        highest_level = 0
        highest_degree = "Unknown"
        
        for edu in education_list:
            if isinstance(edu, dict):
                degree = edu.get('degree', '').lower()
            else:
                degree = str(edu).lower()
            
            for level_name, level_value in education_levels.items():
                if level_name in degree:
                    if level_value > highest_level:
                        highest_level = level_value
                        highest_degree = level_name.title()
                    break
        
        return highest_degree if highest_level > 0 else "N/A"
