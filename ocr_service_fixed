import io
import json
import tempfile
import os
from google.cloud import vision
from google.oauth2 import service_account
import streamlit as st

class OCRServiceFixed:
    """Enhanced OCR service with better error handling and debugging"""
    
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
        """Test the Google Cloud Vision API connection with minimal call"""
        try:
            # Create a minimal test image (1x1 white pixel)
            from PIL import Image
            test_image = Image.new('RGB', (50, 20), color='white')
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            test_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Make a minimal request - just check if API responds
            response = self.client.text_detection(image=vision_image)
            
            # Check for errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API test failed: {response.error.message}")
                
            st.success("✅ Google Cloud Vision API connection successful")
                
        except Exception as e:
            st.error(f"❌ Google Cloud Vision API connection test failed: {str(e)}")
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
            
            # Ensure image is in RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as PNG with high quality
            image.save(img_byte_arr, format='PNG', optimize=False)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Debug: Check image size
            image_size_kb = len(img_byte_arr) / 1024
            st.info(f"Processing image: {image.size[0]}x{image.size[1]} pixels, {image_size_kb:.1f} KB")
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Perform text detection
            response = self.client.text_detection(image=vision_image)
            
            # Check for API errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API error: {response.error.message}")
            
            texts = response.text_annotations
            
            # Debug: Show detection results
            st.info(f"OCR found {len(texts)} text annotations")
            
            # Extract text from response
            if texts:
                # First annotation contains the entire text
                extracted_text = texts[0].description
                if extracted_text:
                    # Debug: Show extracted text length
                    st.success(f"Extracted {len(extracted_text)} characters of text")
                    return extracted_text.strip()
                else:
                    st.warning("OCR response was empty")
                    return ""
            else:
                st.warning("No text detected in image")
                return ""
                
        except Exception as e:
            error_msg = f"Error extracting text from image: {str(e)}"
            st.error(error_msg)
            raise Exception(error_msg)
    
    def extract_text_batch(self, images):
        """
        Extract text from multiple images in sequence
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of extracted text strings
        """
        texts = []
        total_images = len(images)
        
        for i, image in enumerate(images):
            try:
                st.info(f"Processing page {i+1} of {total_images}...")
                text = self.extract_text_from_image(image)
                texts.append(text)
            except Exception as e:
                st.warning(f"Failed to extract text from page {i+1}: {str(e)}")
                texts.append("")  # Add empty string for failed page
                
        return texts
    
    def get_text_with_confidence(self, image):
        """
        Extract text with confidence scores
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with text and confidence information
        """
        try:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Perform document text detection for detailed info
            response = self.client.document_text_detection(image=vision_image)
            
            # Check for API errors
            if response.error.message:
                raise Exception(f"Google Cloud Vision API error: {response.error.message}")
            
            result = {
                "text": "",
                "confidence": 0.0,
                "word_count": 0
            }
            
            if response.full_text_annotation:
                result["text"] = response.full_text_annotation.text
                
                # Calculate average confidence
                total_confidence = 0
                word_count = 0
                
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                total_confidence += word.confidence
                                word_count += 1
                
                if word_count > 0:
                    result["confidence"] = total_confidence / word_count
                    result["word_count"] = word_count
            
            return result
            
        except Exception as e:
            st.error(f"Error getting text with confidence: {str(e)}")
            return {"text": "", "confidence": 0.0, "word_count": 0}
