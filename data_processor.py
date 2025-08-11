import re
from dateutil import parser
from datetime import datetime, timedelta
import logging

class DataProcessor:
    """Process and clean extracted data"""
    
    def clean_text(self, text):
        """Clean and normalize text for better NER processing"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with NER
        text = re.sub(r'[^\w\s@.,()-]', ' ', text)
        
        # Normalize spacing around punctuation
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        text = re.sub(r'([,.!?])\s*', r'\1 ', text)
        
        return text.strip()
    
    def process_employment_history(self, text, organizations, job_titles):
        """Process employment history to determine current vs previous positions"""
        
        # Initialize result
        result = {
            'current_job_title': '',
            'current_company': '',
            'previous_job_titles': '',
            'previous_companies': ''
        }
        
        try:
            # Extract dates and associate with positions
            employment_entries = self._extract_employment_entries(text)
            
            # Sort by date to determine current vs previous
            if employment_entries:
                # Most recent entry is current
                current_entry = employment_entries[0]
                result['current_job_title'] = current_entry.get('title', '')
                result['current_company'] = current_entry.get('company', '')
                
                # Previous entries
                if len(employment_entries) > 1:
                    previous_titles = []
                    previous_companies = []
                    
                    for entry in employment_entries[1:]:
                        if entry.get('title'):
                            previous_titles.append(entry['title'])
                        if entry.get('company'):
                            previous_companies.append(entry['company'])
                    
                    result['previous_job_titles'] = ' | '.join(previous_titles)
                    result['previous_companies'] = ' | '.join(previous_companies)
            
            # Fallback: use first found items if no date-based sorting possible
            elif organizations or job_titles:
                if job_titles:
                    result['current_job_title'] = job_titles[0]
                    if len(job_titles) > 1:
                        result['previous_job_titles'] = ' | '.join(job_titles[1:])
                
                if organizations:
                    result['current_company'] = organizations[0]
                    if len(organizations) > 1:
                        result['previous_companies'] = ' | '.join(organizations[1:])
        
        except Exception as e:
            logging.error(f"Error processing employment history: {e}")
        
        return result
    
    def _extract_employment_entries(self, text):
        """Extract employment entries with dates"""
        entries = []
        
        try:
            # Split text into sections that might contain employment info
            sections = re.split(r'\n\s*\n', text)
            
            for section in sections:
                # Look for date patterns
                dates = self._extract_dates_from_section(section)
                if not dates:
                    continue
                
                # Look for company/organization names (often capitalized)
                companies = re.findall(r'\b[A-Z][A-Za-z\s&.,]{2,30}(?:Inc|Ltd|LLC|Corp|Company|Group|Solutions|Services|Technologies)\b', section)
                
                # Look for job titles (common patterns)
                title_patterns = [
                    r'\b(?:Senior|Junior|Lead|Principal|Chief|Head of|Director of|Manager of|VP of)\s+[A-Za-z\s]{2,30}\b',
                    r'\b[A-Za-z\s]{2,30}(?:Manager|Director|Engineer|Developer|Analyst|Specialist|Coordinator|Assistant|Executive|Officer)\b',
                    r'\b(?:Software|Hardware|Data|Business|Product|Project|Marketing|Sales|HR|IT|Finance)\s+[A-Za-z\s]{2,30}\b'
                ]
                
                titles = []
                for pattern in title_patterns:
                    titles.extend(re.findall(pattern, section, re.IGNORECASE))
                
                # Create entry if we have meaningful data
                if companies or titles:
                    entry = {
                        'date': max(dates) if dates else datetime.min,
                        'company': companies[0] if companies else '',
                        'title': titles[0] if titles else '',
                        'raw_text': section[:200]  # Keep sample for debugging
                    }
                    entries.append(entry)
            
            # Sort by date (most recent first)
            entries.sort(key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error extracting employment entries: {e}")
        
        return entries
    
    def _extract_dates_from_section(self, section):
        """Extract dates from a text section"""
        dates = []
        
        # Date patterns to look for
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # Month YYYY
            r'\b\d{4}\s*-\s*\d{4}\b',      # YYYY - YYYY
            r'\b\d{4}\s*to\s*\d{4}\b',     # YYYY to YYYY
            r'\b\d{4}\s*–\s*\d{4}\b',      # YYYY – YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, section, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    if '-' in match and len(match.split('-')) == 2:
                        # Handle year ranges
                        years = match.split('-')
                        parsed_date = datetime(int(years[1].strip()), 12, 31)
                    elif 'to' in match.lower():
                        years = re.findall(r'\d{4}', match)
                        if len(years) >= 2:
                            parsed_date = datetime(int(years[1]), 12, 31)
                        else:
                            continue
                    else:
                        parsed_date = parser.parse(match, fuzzy=True)
                    
                    dates.append(parsed_date)
                except:
                    continue
        
        return dates
