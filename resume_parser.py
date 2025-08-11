import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

class HuggingFaceResumeParser:
    def __init__(self, model_name="yashpwr/resume-ner-bert-v2"):
        # Load model & tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple"
        )

    def parse(self, text):
        # Run NER
        entities = self.ner_pipeline(text)

        # Prepare result
        result = {
            "first_name": "",
            "last_name": "",
            "email": self.extract_email(text),
            "phone": self.extract_phone(text),
            "current_job_title": "",
            "current_company": ""
        }

        # Extract names, job titles, companies from model output
        for ent in entities:
            label = ent["entity_group"].upper()
            value = ent["word"].replace("##", "").strip()

            if label in ["PER", "PERSON", "NAME"]:
                parts = value.split()
                if parts:
                    result["first_name"] = parts[0]
                    if len(parts) > 1:
                        result["last_name"] = " ".join(parts[1:])
            elif label in ["JOB", "TITLE", "POSITION", "ROLE"] and not result["current_job_title"]:
                result["current_job_title"] = value
            elif label in ["ORG", "ORGANIZATION", "COMPANY"] and not result["current_company"]:
                result["current_company"] = value

        return result

    @staticmethod
    def extract_email(text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""

    @staticmethod
    def extract_phone(text):
        phone_pattern = r'(\+?\d[\d\s\-]{7,}\d)'
        matches = re.findall(phone_pattern, text)
        return matches[0].strip() if matches else ""

# Example usage
if __name__ == "__main__":
    parser = HuggingFaceResumeParser()
    resume_text = """
    John Smith is a Senior Software Engineer at Google with 8 years of experience.
    Contact: john.smith@gmail.com, +61 412 345 678
    """
    result = parser.parse(resume_text)
    print(result)
