import os
import PIL
import structlog
import google.generativeai as genai
import tenacity

from config.logger import setup_logging

class ImageOCRProcessor:
    """
    A class to handle OCR processing of images.
    """
    def __init__(self, logger):
        """
        Initializes the ImageOCRProcessor with an optional logger.
        """
        self.logger = logger if logger else structlog.get_logger(__name__) # Use provided logger or create a default

    @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2)) # Retry 3 times, wait 2 seconds between retries
    def _get_ocr_response(self, model, prompt, image):
        """
        Helper function with retry logic
        """
        response = model.generate_content([prompt, image])
        response.resolve()
        return response.text

    def extract_text_from_image(self, image_path: str, model: genai.GenerativeModel, prompt: str) -> str:
        """
        Extracts text from a single image using OCR.
        """
        try:
            image = PIL.Image.open(image_path)
            raw_response_text = self._get_ocr_response(model, prompt, image) # Use helper function with retry
            return raw_response_text
        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {e}")
            return f"Error during OCR: {e}"

    def perform_ocr(self, client,base_path: str, suffix: str, model_name: str, save_output: bool = True) -> dict:
        """
        Performs OCR on images in the given path, optionally saves output to text files,
        and returns a dictionary with filenames as keys and OCR text as values.
        """
        ocr_results = {} # Initialize an empty dictionary to store results
        try:
            image_paths = [os.path.join(base_path, f) for f in os.listdir(base_path) if f.endswith(suffix)]
            image_paths.sort()
            model = genai.GenerativeModel(model_name=model_name)
            prompt = "ocr the following image"

            for image_path in image_paths:
                ocr_text = self.extract_text_from_image(image_path, model, prompt)
                filename = os.path.basename(image_path) # Get filename for dictionary key
                ocr_results[filename] = ocr_text # Store result in dictionary
                self.logger.info(f"Extracted text from {image_path}: {ocr_text}")

                if save_output:
                    txt_file_path = os.path.join(base_path, f"{os.path.basename(image_path).split('.')[0]}.txt")
                    with open(txt_file_path, "w") as f:
                        f.write(ocr_text)
                    print(f"OCR text saved to: {txt_file_path}")
                else:
                    print(f"OCR Text from {image_path}:\n{ocr_text}")

            print("OCR processing complete.")
            return ocr_results # Return the dictionary
        except Exception as e:
            self.logger.error(f"Error during OCR: {e}")
            return ocr_results # Return potentially partial results even on error

if __name__ == "__main__": # Added main block for testing
    setup_logging()
    logger = structlog.get_logger(__name__)
    processor = ImageOCRProcessor(logger)
    base_path = "/home/xbloc/Respos/aidevs3python/documents/pliki_z_fabryki"  # <--- Set your test directory here
    suffix = ".png"         # <--- Set your image suffix here
    model_name = "gemini-2.0-flash-exp" # <--- Choose your Gemini model
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    print("--- Performing OCR and saving to files, getting dictionary output ---")
    ocr_dictionary_output = processor.perform_ocr(client, base_path, suffix, model_name, save_output=False)
    print("\n--- OCR Dictionary Output (saving to files was also enabled): ---")
    for filename, text in ocr_dictionary_output.items():
        print(f"{filename}:")
        print(text)
        print("-" * 20)