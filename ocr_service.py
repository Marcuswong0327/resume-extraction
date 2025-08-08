import io
import json
import tempfile
import os
from google.cloud import vision
from google.oauth2 import service_account
import streamlit as st

class OCRService:
    """Handles Google Cloud Vision API OCR operations"""
    
    def __init__(self, credentials_dict):
        """
        Initialize OCR service with Google Cloud credentials
        
        Args:
            credentials_dict: Dictionary containing GCP service account credentials
        """
        try:
            # Validate required fields
            required_fields = ["type", "project_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if field not in credentials_dict]
            
            if missing_fields:
                raise ValueError(f"Missing required credential fields: {missing_fields}")
            
            # Create credentials from dictionary
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
            
            # Initialize Vision API client
            self.client = vision.ImageAnnotatorClient(credentials=self.credentials)
            
            # Test the connection
            self._test_connection()
            
        except Exception as e:
            st.error(f"Error initializing Google Cloud Vision client: {str(e)}")
            raise e
    
    def _test_connection(self):
        """Test the Google Cloud Vision API connection"""
        try:
            # Create a simple test image (1x1 white pixel)
            from PIL import Image
            test_image = Image.new('RGB', (1, 1), color='white')
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            test_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Make a simple request
            response = self.client.text_detection(image=vision_image)
            
            # Check for errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API test failed: {response.error.message}")
                
        except Exception as e:
            raise Exception(f"Google Cloud Vision API connection test failed: {str(e)}")
    
    def extract_text_from_image(self, image):
        """
        Extract text from PIL image using Google Cloud Vision API
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        try:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Perform text detection
            response = self.client.text_detection(image=vision_image)
            
            # Check for API errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API error: {response.error.message}")
            
            texts = response.text_annotations
            
            # Extract text from response
            if texts:
                # First annotation contains the entire text
                extracted_text = texts[0].description
                return extracted_text.strip() if extracted_text else ""
            else:
                return ""
                
        except Exception as e:
            st.error(f"Error extracting text from image: {str(e)}")
            raise e
    
    def extract_text_with_confidence(self, image):
        """
        Extract text with confidence scores using Google Cloud Vision API
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with text and confidence information
        """
        try:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Perform document text detection for better structure
            response = self.client.document_text_detection(image=vision_image)
            
            # Check for API errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API error: {response.error.message}")
            
            document = response.full_text_annotation
            
            if not document:
                return {"text": "", "confidence": 0.0, "pages": []}
            
            # Extract structured text information
            result = {
                "text": document.text,
                "confidence": 0.0,
                "pages": []
            }
            
            # Calculate average confidence
            total_confidence = 0
            word_count = 0
            
            for page in document.pages:
                page_info = {
                    "width": page.width,
                    "height": page.height,
                    "blocks": []
                }
                
                for block in page.blocks:
                    block_text = ""
                    block_confidence = 0
                    block_word_count = 0
                    
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            block_text += word_text + " "
                            block_confidence += word.confidence
                            block_word_count += 1
                            total_confidence += word.confidence
                            word_count += 1
                    
                    if block_word_count > 0:
                        block_info = {
                            "text": block_text.strip(),
                            "confidence": block_confidence / block_word_count
                        }
                        page_info["blocks"].append(block_info)
                
                result["pages"].append(page_info)
            
            if word_count > 0:
                result["confidence"] = total_confidence / word_count
            
            return result
            
        except Exception as e:
            st.error(f"Error extracting text with confidence: {str(e)}")
            # Fallback to simple text detection
            return {
                "text": self.extract_text_from_image(image),
                "confidence": 0.0,
                "pages": []
            }
