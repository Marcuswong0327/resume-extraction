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
                # Create summary sheet
                self._create_summary_sheet(candidates_data, writer)
                
                # Create detailed sheets for each candidate
                self._create_detailed_sheets(candidates_data, writer)
                
                # Create skills analysis sheet
                self._create_skills_analysis_sheet(candidates_data, writer)
                
                # Create comparison sheet
                self._create_comparison_sheet(candidates_data, writer)
            
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
            # Get skills as comma-separated string
            skills = candidate.get('skills', [])
            skills_str = ', '.join(skills[:10])  # Limit to first 10 skills for readability
            if len(skills) > 10:
                skills_str += f" (and {len(skills) - 10} more)"
            
            summary_row = {
                'Candidate_ID': i,
                'Name': candidate.get('name', 'N/A'),
                'Email': candidate.get('email', 'N/A'),
                'Phone': candidate.get('phone', 'N/A'),
                'Total_Skills': len(skills),
                'Top_Skills': skills_str,
                'Work_Experience_Count': len(candidate.get('experience', [])),
                'Education_Count': len(candidate.get('education', [])),
                'Has_Summary': 'Yes' if candidate.get('summary', '').strip() else 'No',
                'Source_File': candidate.get('filename', 'N/A')
            }
            summary_data.append(summary_row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Auto-adjust column widths
        self._adjust_column_widths(writer.sheets['Summary'])
    
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
                    sheet_name = f"C_{i}"
                
                # Prepare detailed data
                detailed_data = []
                
                # Basic information
                basic_info = [
                    {'Category': 'Personal Info', 'Field': 'Name', 'Value': candidate.get('name', 'N/A')},
                    {'Category': 'Personal Info', 'Field': 'Email', 'Value': candidate.get('email', 'N/A')},
                    {'Category': 'Personal Info', 'Field': 'Phone', 'Value': candidate.get('phone', 'N/A')},
                    {'Category': 'Personal Info', 'Field': 'Source File', 'Value': candidate.get('filename', 'N/A')},
                ]
                detailed_data.extend(basic_info)
                
                # Summary
                if candidate.get('summary', '').strip():
                    detailed_data.append({
                        'Category': 'Summary', 
                        'Field': 'Professional Summary', 
                        'Value': candidate.get('summary', 'N/A')
                    })
                
                # Skills
                skills = candidate.get('skills', [])
                if skills:
                    detailed_data.append({
                        'Category': 'Skills', 
                        'Field': 'All Skills', 
                        'Value': '; '.join(skills)
                    })
                
                # Work Experience
                experience = candidate.get('experience', [])
                if experience:
                    for j, exp in enumerate(experience, 1):
                        if isinstance(exp, dict):
                            exp_text = self._format_experience_for_excel(exp)
                        else:
                            exp_text = str(exp)
                        
                        detailed_data.append({
                            'Category': 'Experience', 
                            'Field': f'Job {j}', 
                            'Value': exp_text
                        })
                
                # Education
                education = candidate.get('education', [])
                if education:
                    for j, edu in enumerate(education, 1):
                        if isinstance(edu, dict):
                            edu_text = self._format_education_for_excel(edu)
                        else:
                            edu_text = str(edu)
                        
                        detailed_data.append({
                            'Category': 'Education', 
                            'Field': f'Education {j}', 
                            'Value': edu_text
                        })
                
                # Create DataFrame and export
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Auto-adjust column widths
                self._adjust_column_widths(writer.sheets[sheet_name])
                    
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
            
            for candidate in candidates_data:
                skills = candidate.get('skills', [])
                for skill in skills:
                    if skill in skills_count:
                        skills_count[skill] += 1
                    else:
                        skills_count[skill] = 1
            
            # Create skills frequency data
            skills_frequency_data = []
            total_candidates = len(candidates_data)
            
            for skill, count in sorted(skills_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_candidates) * 100
                skills_frequency_data.append({
                    'Skill': skill,
                    'Candidate_Count': count,
                    'Total_Candidates': total_candidates,
                    'Percentage': f"{percentage:.1f}%",
                    'Frequency_Score': round(percentage, 1)
                })
            
            skills_df = pd.DataFrame(skills_frequency_data)
            skills_df.to_excel(writer, sheet_name='Skills_Analysis', index=False)
            
            # Auto-adjust column widths
            self._adjust_column_widths(writer.sheets['Skills_Analysis'])
                
        except Exception as e:
            st.warning(f"Error creating skills analysis sheet: {str(e)}")
    
    def _create_comparison_sheet(self, candidates_data: List[Dict], writer):
        """
        Create comparison sheet for candidate evaluation
        
        Args:
            candidates_data: List of candidate data
            writer: Excel writer object
        """
        try:
            comparison_data = []
            
            for i, candidate in enumerate(candidates_data, 1):
                skills = candidate.get('skills', [])
                experience = candidate.get('experience', [])
                education = candidate.get('education', [])
                
                # Calculate some metrics
                programming_skills = self._count_programming_skills(skills)
                has_degree = any('bachelor' in str(edu).lower() or 'master' in str(edu).lower() 
                               or 'phd' in str(edu).lower() for edu in education)
                
                comparison_row = {
                    'Rank': i,
                    'Candidate_ID': i,
                    'Name': candidate.get('name', 'N/A'),
                    'Email': candidate.get('email', 'N/A'),
                    'Phone': candidate.get('phone', 'N/A'),
                    'Total_Skills': len(skills),
                    'Programming_Skills': programming_skills,
                    'Experience_Entries': len(experience),
                    'Education_Entries': len(education),
                    'Has_Degree': 'Yes' if has_degree else 'No',
                    'Has_Contact_Info': 'Yes' if candidate.get('email') or candidate.get('phone') else 'No',
                    'Has_Summary': 'Yes' if candidate.get('summary', '').strip() else 'No',
                    'Completeness_Score': self._calculate_completeness_score(candidate),
                    'Source_File': candidate.get('filename', 'N/A')
                }
                comparison_data.append(comparison_row)
            
            # Sort by completeness score
            comparison_data.sort(key=lambda x: x['Completeness_Score'], reverse=True)
            
            # Update rank after sorting
            for i, row in enumerate(comparison_data, 1):
                row['Rank'] = i
            
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df.to_excel(writer, sheet_name='Comparison', index=False)
            
            # Auto-adjust column widths
            self._adjust_column_widths(writer.sheets['Comparison'])
            
        except Exception as e:
            st.warning(f"Error creating comparison sheet: {str(e)}")
    
    def _format_experience_for_excel(self, exp_dict: Dict) -> str:
        """Format experience dictionary for Excel display"""
        parts = []
        
        position = exp_dict.get('position', '').strip()
        company = exp_dict.get('company', '').strip()
        duration = exp_dict.get('duration', '').strip()
        description = exp_dict.get('description', '').strip()
        
        if position and company:
            parts.append(f"{position} at {company}")
        elif position:
            parts.append(position)
        elif company:
            parts.append(company)
        
        if duration:
            parts.append(f"Duration: {duration}")
        
        if description:
            if len(description) > 300:
                description = description[:300] + "..."
            parts.append(f"Description: {description}")
        
        return " | ".join(parts) if parts else "N/A"
    
    def _format_education_for_excel(self, edu_dict: Dict) -> str:
        """Format education dictionary for Excel display"""
        parts = []
        
        degree = edu_dict.get('degree', '').strip()
        field = edu_dict.get('field', '').strip()
        institution = edu_dict.get('institution', '').strip()
        year = edu_dict.get('year', '').strip()
        
        if degree and field:
            parts.append(f"{degree} in {field}")
        elif degree:
            parts.append(degree)
        elif field:
            parts.append(field)
        
        if institution:
            parts.append(f"from {institution}")
        
        if year:
            parts.append(f"({year})")
        
        return " ".join(parts) if parts else "N/A"
    
    def _count_programming_skills(self, skills: List[str]) -> int:
        """Count programming-related skills"""
        programming_keywords = [
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'typescript', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css'
        ]
        
        count = 0
        for skill in skills:
            if any(keyword in skill.lower() for keyword in programming_keywords):
                count += 1
        
        return count
    
    def _calculate_completeness_score(self, candidate: Dict) -> float:
        """Calculate a completeness score for the candidate (0-100)"""
        score = 0
        
        # Name (20 points)
        if candidate.get('name', '').strip():
            score += 20
        
        # Contact info (20 points)
        if candidate.get('email', '').strip():
            score += 10
        if candidate.get('phone', '').strip():
            score += 10
        
        # Skills (20 points)
        skills_count = len(candidate.get('skills', []))
        if skills_count > 0:
            score += min(20, skills_count * 2)  # 2 points per skill, max 20
        
        # Experience (20 points)
        experience_count = len(candidate.get('experience', []))
        if experience_count > 0:
            score += min(20, experience_count * 5)  # 5 points per experience, max 20
        
        # Education (10 points)
        education_count = len(candidate.get('education', []))
        if education_count > 0:
            score += min(10, education_count * 5)  # 5 points per education, max 10
        
        # Summary (10 points)
        if candidate.get('summary', '').strip():
            score += 10
        
        return round(score, 1)
    
    def _adjust_column_widths(self, worksheet):
        """Auto-adjust column widths for better readability"""
        try:
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
                adjusted_width = min(max_length + 2, 100)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
        except Exception as e:
            pass  # Ignore errors in column width adjustment
