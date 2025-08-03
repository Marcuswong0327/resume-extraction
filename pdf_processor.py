import io
from pdf2image import convert_from_bytes
from PIL import Image
import streamlit as st

class PDFProcessor:
    """Handles PDF to image conversion for OCR processing"""
    
    def __init__(self):
        self.dpi = 300  # High DPI for better OCR accuracy
    
    def pdf_to_images(self, uploaded_file):
        """
        Convert PDF file to list of PIL images
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            List of PIL Image objects
        """
        try:
            # Read PDF bytes
            pdf_bytes = uploaded_file.read()
            
            # Convert PDF to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                output_folder=None,
                thread_count=1
            )
            
            # Convert to RGB if necessary (some PDFs might be in CMYK)
            processed_images = []
            for image in images:
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                processed_images.append(image)
            
            return processed_images
            
        except Exception as e:
            st.error(f"Error converting PDF to images: {str(e)}")
            raise e
    
    def optimize_image_for_ocr(self, image):
        """
        Optimize image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Optimized PIL Image object
        """
        try:
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if image is too large (OCR works better on reasonably sized images)
            width, height = image.size
            if width > 2000 or height > 2000:
                # Calculate new size maintaining aspect ratio
                if width > height:
                    new_width = 2000
                    new_height = int((height * 2000) / width)
                else:
                    new_height = 2000
                    new_width = int((width * 2000) / height)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            st.error(f"Error optimizing image for OCR: {str(e)}")
            return image
    
    def image_to_bytes(self, image, format='PNG'):
        """
        Convert PIL image to bytes for API calls
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Bytes representation of the image
        """
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format)
            img_byte_arr = img_byte_arr.getvalue()
            return img_byte_arr
            
        except Exception as e:
            st.error(f"Error converting image to bytes: {str(e)}")
            raise e
