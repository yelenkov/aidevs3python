import os
import sys
import PIL
import structlog
import google.generativeai as genai

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from config.logger import setup_logging

class ImageOCRProcessor:
    """
    A class to handle OCR processing of images.
    """
    def __init__(self, logger):
        """
        Initializes the ImageOCRProcessor with an optional logger.
        """
        self.logger = logger if logger else structlog.get_logger(__name__)

    def extract_text_from_image(self, image_path: str, model: genai.GenerativeModel, prompt: str) -> str:
        """
        Extracts text from a single image using OCR.
        """
        logger = self.logger
        logger.info(f"Starting text extraction from {image_path}")
        try:
            image = PIL.Image.open(image_path)
            response = model.generate_content([prompt, image])
            response.resolve()
            raw_response_text = response.text
            logger.info(f"Extracted text from {image_path}: {raw_response_text}")
            return raw_response_text
        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {e}")
            return f"Error during OCR: {e}"

    def perform_ocr(self, client, file_path: str, model_name: str, save_output: bool = False) -> dict:
        """
        Performs OCR on a single image file.

        Args:
            client: The client for interacting with the Gemini API.
            file_path (str): The full path to the image file to process.
            model_name (str): The name of the Gemini model to use.
            save_output (bool, optional): Whether to save the OCR text to a file. Defaults to False.

        Returns:
            dict: A dictionary with the filename as key and OCR text as value, or an empty dictionary on error.
        """
        logger = self.logger
        logger.info("Starting OCR processing for a single file")
        ocr_results = {} # Initialize an empty dictionary to store results
        try:
            model = genai.GenerativeModel(model_name=model_name)
            prompt = "Extract text from the following image, do not include any other information, just the text."

            ocr_text = self.extract_text_from_image(file_path, model, prompt)
            filename = os.path.basename(file_path) # Get filename for dictionary key
            ocr_results[filename] = ocr_text # Store result in dictionary
            logger.info(f"Extracted text from {file_path}: {ocr_text}")

            if save_output:
                txt_file_path = os.path.join(os.path.dirname(file_path), f"{os.path.basename(file_path).split('.')[0]}.txt")
                with open(txt_file_path, "w") as f:
                    f.write(ocr_text)
                logger.info(f"OCR text saved to: {txt_file_path}")
            else:
                logger.info(f"OCR Text from {file_path}:\n{ocr_text}")

            logger.info("OCR processing complete for single file.")
            return ocr_results
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return ocr_results

    def process_images_in_directory(self, client, base_path: str, model_name: str, save_output: bool = False) -> dict:
        """
        Processes all image files in a given directory using OCR.

        Args:
            client: The client for interacting with the Gemini API.
            base_path (str): The path to the directory containing image files.
            model_name (str): The name of the Gemini model to use for OCR.
            save_output (bool, optional): Whether to save the OCR text to files. Defaults to False.

        Returns:
            dict: A dictionary containing OCR results for each processed image file,
                  with filenames as keys and OCR text as values.
        """
        logger = self.logger
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'] # <--- Add or modify extensions as needed
        ocr_dictionary_output = {} # Initialize an empty dictionary to store all OCR results

        for filename in os.listdir(base_path):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                file_path = os.path.join(base_path, filename)
                logger.info(f"Processing image file: {filename}, file_path: {file_path}")
                file_ocr_result = self.perform_ocr(client, file_path, model_name, save_output=save_output) # Process single file
                ocr_dictionary_output.update(file_ocr_result) # Add result to the dictionary

        logger.info("Image directory processing complete.")
        return ocr_dictionary_output

if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    processor = ImageOCRProcessor(logger)
    base_path = "documents/pliki_z_fabryki"  # <--- Set your base path here
    model_name = "gemini-2.0-flash" # <--- Choose your Gemini model
    client = genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    ocr_results = processor.process_images_in_directory(client, base_path, model_name, save_output=True)