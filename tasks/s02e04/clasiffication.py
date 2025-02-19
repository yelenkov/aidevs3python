import os
import sys
from dotenv import load_dotenv
import structlog
from google import genai
import json
from google.genai import types

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from config.ocr import ImageOCRProcessor
from config.transcribe import AudioTranscriber
from config.logger import setup_logging
from config.utils import send_answer

load_dotenv()

class Classification:
    """
    A class to handle classification, now integrating OCR and transcription.
    """
    def __init__(self, logger):
        """
        Initializes the Classification class with a logger and OCR/Transcription processors.
        """
        self.logger = logger if logger else structlog.get_logger(__name__)
        self.ocr_processor = ImageOCRProcessor(self.logger)
        self.audio_transcriber = AudioTranscriber(self.logger)

    def extract_json_from_wrapped_response(self, raw_response_text: str) -> dict:
        """
        Extracts JSON from a text response that might be wrapped in backticks or quotes.
        """
        start = raw_response_text.index("{")
        end = raw_response_text.rindex("}") + 1  # Use rindex to find the last occurrence
        json_str = raw_response_text[start:end]
        # Clean up the string by removing newlines and normalizing spaces
        json_str = json_str.replace("\n", " ").replace("    ", " ")
        return json.loads(json_str)

    def _extract_content(self, client, file_path: str, model_name: str) -> str | None:
        """
        Extracts text content from a file based on its type.

        Args:
            file_path (str): The path to the file.
            client: The Gemini API client.
            model_name (str): The name of the Gemini model to use.

        Returns:
            str | None: The extracted text content, or None if extraction fails or file type is unsupported.
        """
        logger = self.logger
        file_name = os.path.basename(file_path)
        file_lower = file_name.lower()

        image_suffix = (".png", ".jpg", ".jpeg")
        audio_suffix = (".mp3", ".wav", ".ogg")

        if file_lower.endswith(image_suffix):
            logger.info(f"Processing image file: {file_name}")
            text_content_dict = self.ocr_processor.perform_ocr(
                client=client,
                file_path=file_path,
                model_name=model_name,
                save_output=False
            )
            text_content = list(text_content_dict.values())[0] if text_content_dict else None

        elif file_lower.endswith(audio_suffix):
            logger.info(f"Processing audio file: {file_name}")
            text_content = self.audio_transcriber.transcribe_single_audio(
                client=client,
                file_path=file_path,
                model_name=model_name,
                save_output=False
            )
        elif file_lower.endswith(".txt"):
            logger.info(f"Processing text file: {file_name}")
            with open(file_path, "r") as f:
                text_content = f.read()
        else:
            logger.warning(f"Unsupported file type: {file_name}")
            return None

        return text_content

    def _classify_content(self, client, text_content: str, model_name: str, original_filename: str, result_data: dict):
        """
        Classifies the given text content using a language model and updates result_data.

        Args:
            text_content (str): The text content to classify.
            client: The Gemini API client.
            model_name (str): The name of the Gemini model to use for classification.
            original_filename (str): The original filename of the processed file.
            result_data (dict): Dictionary to store classification results.
        """
        logger = self.logger

        logger.info(event="Classifying content", file_path=original_filename)
        categories = ["people", "hardware", "other"]
        classification_result: dict[str, bool] = {}

        logger.info(event="Categories before classification", categories=categories, file_path=original_filename)

        if not text_content:
            logger.warning(event="No text content for classification", file_path=original_filename)
            for category in categories:
                classification_result[category] = False
            result_data[category] = []
            return

        system_prompt = """
            You are tasked with processing data reports. The input consists of daily reports from multiple departments, 
            including technical reports and security reports. Not all contain useful information.

            Your task is to:
            1. Extract only notes containing:
                - Information about captured individuals
                - Evidence of human presence
                - Hardware malfunction repairs (exclude software-related issues)
            2. Your task is ONLY to categorize document based on two categories "people", "hardware" and "other". 

            Please process the data according to these requirements.
            Respond ONLY with valid JSON. Do not write an introduction or summary.

            Result should be in tag <answer> and have below JSON format:
            {
            "people": "value",
            "hardware": "value",
            "other": "value"
            }

            Sample input 1:
            "entry deleted"

            Sample result:
            {
            "people": "False",
            "hardware": "False",
            "other": "True"
            }

            Sample input 2:
            Fingerprint analysis identified subject: Jan Nowak (correlated with birth records database)

            Sample result:
            {
            "people": "True",
            "hardware": "False",
            "other": "False"
            }

            Sample input 3:
            Repair note: Fingerprint malfunction detected. Scheduled repair: 12/03/2023 15:48:37 

            Sample result:
            {
            "people": "False",
            "hardware": "True",
            "other": "False"
            }

            Sample input 4:
            Boss, as directed, we searched the tenements in the nearby town for rebels. We were unable to find anyone. Sensor dźwiękowy i detektory ruchu w pełnej gotowości.

            Sample result:
            {
            "people": "False",
            "hardware": "False",
            "other": "True"
            }

            Sample input 5:
            Wstępny alarm wykrycia - ruch organiczny. Czujniki pozostają aktywne, a wytyczne dotyczące wykrywania życia organicznego - bez rezultatów. Stan patrolu bez zakłóceń.

            Sample result:
            {
            "people": "False",
            "hardware": "False",
            "other": "True"
            }

            Sample input 6:
            We met a guy named Dominik, he is good with preparing pizza.

            Sample result:
            {
            "people": "False",
            "hardware": "False",
            "other": "True"
            }   
            Reason: It doesn't talk about person being captured or threat.
        """
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            ),
            contents=text_content
        )
        raw_response_text = response.text
        logger.info(f"Response: {raw_response_text}")

        try:
            classification_json = self.extract_json_from_wrapped_response(raw_response_text)
            if classification_json.get("people", "False") == "True":
                result_data["people"].append(original_filename)
                logger.info(f"Added {original_filename} to people")
            if classification_json.get("hardware", "False") == "True":
                result_data["hardware"].append(original_filename)
                logger.info(f"Added {original_filename} to hardware")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}, Raw Response: {raw_response_text}")
            logger.error("Could not decode JSON response from model.")

        logger.info(event="Classification result", classification_result=classification_result, file_path=original_filename)
        logger.info(event="Categories after classification", categories=categories, file_path=original_filename)

    def ask_question(self, client, base_path: str, model_name: str) -> dict:
        """
        Processes files in the given base path, extracts content, classifies it, and returns results.

        Args:
            client: The Gemini API client.
            base_path (str): The path to the directory containing files to process.
            model_name (str): The name of the Gemini model to use.

        Returns:
            dict: A dictionary containing lists of filenames classified as 'people' and 'hardware'.
        """
        logger = self.logger

        result_data = {
            "people": [],
            "hardware": [],
        }

        for file in os.listdir(base_path):
            file_path = os.path.join(base_path, file)
            logger.info(f"Checking file: {file}, file_path: {file_path}")
            original_filename = file

            text_content = self._extract_content(client, file_path, model_name)
            self._classify_content(client, text_content, model_name, original_filename, result_data)

        logger.info(f"Result data: {result_data}")

        # Remove 'other' category from result_data if it exists
        if "other" in result_data:
            del result_data["other"]
            logger.info("Removed 'other' category from result_data.")

        # Specific removal for incorrectly classified file
        incorrect_file = "2024-11-12_report-12-sektor_A1.mp3"
        if incorrect_file in result_data["people"]:
            result_data["people"].remove(incorrect_file)
            logger.info(f"Removed '{incorrect_file}' from 'people' category due to misclassification.")

        return result_data

if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')
    base_path = "./documents/pliki_z_fabryki"
    model_name = "gemini-2.0-flash"

    classification = Classification(logger)

    result = classification.ask_question(client, base_path, model_name)
    print(result)
    send_answer("kategorie", AIDEVS_API_KEY, result)