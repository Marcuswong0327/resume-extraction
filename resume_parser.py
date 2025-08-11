import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from text_extractor import TextExtractor
from data_processor import DataProcessor
import logging

class ResumeParser:
    """High-performance resume parser using Hugging Face NER models"""
    
    def __init__(self):
        """Initialize the resume parser with pre-trained models"""
        self.text_extractor = TextExtractor()
        self.data_processor = DataProcessor()
        
        # Initialize Hugging Face NER pipeline
        try:
            model_name = "yashpwr/resume-ner-bert-v2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=-1  # Use CPU for better compatibility
            )
            logging.info("NER model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading NER model: {e}")
            raise
    
    def parse_resume(self, file_path):
        """Parse a single resume file and extract structured information"""
        try:
            # Extract text from file
            text = self.text_extractor.extract_text(file_path)
            if not text or len(text.strip()) < 10:
                return self._empty_result()
            
            # Clean and preprocess text
            cleaned_text = self.data_processor.clean_text(text)
            
            # Apply NER model
            ner_results = self.ner_pipeline(cleaned_text)
            
            # Extract structured information
            extracted_data = self._extract_structured_data(text, ner_results)
            
            return extracted_data
            
        except Exception as e:
            logging.error(f"Error parsing resume {file_path}: {e}")
            return self._empty_result()
    
    def _extract_structured_data(self, text, ner_results):
        """Extract and structure data from NER results"""
        
        # Initialize result structure
        result = {
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'email_address': '',
            'current_job_title': '',
            'current_company': '',
            'previous_job_titles': '',
            'previous_companies': ''
        }
        
        # Extract names from NER results
        names = self._extract_names(ner_results)
        if names:
            result['first_name'] = names.get('first_name', '')
            result['last_name'] = names.get('last_name', '')
        
        # Extract contact information using regex (more reliable for structured data)
        result['phone_number'] = self._extract_phone_number(text)
        result['email_address'] = self._extract_email(text)
        
        # Extract job information
        job_info = self._extract_job_information(text, ner_results)
        result.update(job_info)
        
        return result
    
    def _extract_names(self, ner_results):
        """Extract first and last names from NER results"""
        names = {'first_name': '', 'last_name': ''}
        person_entities = []
        
        for entity in ner_results:
            if entity['entity_group'].upper() in ['PER', 'PERSON', 'NAME']:
                person_entities.append(entity['word'].strip())
        
        if person_entities:
            # Take the first person entity and split into first/last name
            full_name = person_entities[0].replace('#', '').strip()
            name_parts = full_name.split()
            
            if len(name_parts) >= 2:
                names['first_name'] = name_parts[0]
                names['last_name'] = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                names['first_name'] = name_parts[0]
        
        return names
    
    def _extract_phone_number(self, text):
        """Extract Australian phone numbers using regex patterns"""
        
        # Australian phone number patterns
        patterns = [
            r'\b0[2-9]\d{2}\s?\d{3}\s?\d{3}\b',  # 02xx xxx xxx, 03xx xxx xxx, etc.
            r'\b04\d{2}\s?\d{3}\s?\d{3}\b',      # Mobile: 04xx xxx xxx
            r'\+61\s?[2-9]\s?\d{4}\s?\d{4}\b',   # International format
            r'\+61\s?4\d{2}\s?\d{3}\s?\d{3}\b',  # International mobile
            r'\b\d{4}\s?\d{3}\s?\d{3}\b'         # Generic 4-3-3 format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Clean up the phone number
                phone = matches[0].replace(' ', ' ').strip()
                # Ensure proper spacing for Australian format
                phone = re.sub(r'(\d{4})(\d{3})(\d{3})', r'\1 \2 \3', phone.replace(' ', ''))
                return phone
        
        return ''
    
    def _extract_email(self, text):
        """Extract email addresses using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ''
    
    def _extract_job_information(self, text, ner_results):
        """Extract current and previous job information"""
        
        # Extract organizations and job titles from NER
        organizations = []
        job_titles = []
        
        for entity in ner_results:
            entity_type = entity['entity_group'].upper()
            entity_text = entity['word'].replace('#', '').strip()
            
            if entity_type in ['ORG', 'ORGANIZATION', 'COMPANY']:
                organizations.append(entity_text)
            elif entity_type in ['JOB', 'TITLE', 'POSITION', 'ROLE']:
                job_titles.append(entity_text)
        
        # Use data processor to determine current vs previous based on dates
        job_info = self.data_processor.process_employment_history(
            text, organizations, job_titles
        )
        
        return job_info
    
    def _empty_result(self):
        """Return empty result structure for failed parsing"""
        return {
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'email_address': '',
            'current_job_title': '',
            'current_company': '',
            'previous_job_titles': '',
            'previous_companies': ''
        }
