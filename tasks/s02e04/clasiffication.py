import os
import sys
from dotenv import load_dotenv
import structlog
from google import genai
import json
from google.genai import types

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)
from config.logger import setup_logging
load_dotenv()

class Classification:
    """
    A class to handle classification.
    """
    def __init__(self, logger):
        """
        Initializes the Classification with a logger.
        """
        self.logger = logger if logger else structlog.get_logger(__name__)

    def extract_json_from_wrapped_response(self, response):
        start = response.index("{")
        end = response.rindex("}") + 1  # Use rindex to find the last occurrence
        json_str = response[start:end]
        # Clean up the string by removing newlines and normalizing spaces
        json_str = json_str.replace("\n", " ").replace("    ", " ")
        return json.loads(json_str)

    def ask_question(self, client, base_path: str, suffix: str, model_name: str):
        logger = self.logger

        result_data = {
            "people": [],
            "hardware": [],
        }

        for file in os.listdir(base_path):
            if file.endswith(suffix):
                logger.info(f"Processing file: {file}")

                filename = file
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

                source = open(os.path.join(base_path, file), "r").read()

                response = client.models.generate_content(
                    model=model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json"
                    ),
                    contents=source
                )

                logger.info(f"Response: {response.text}")

                json_object = self.extract_json_from_wrapped_response(response.text)
                # Iterate through categories we want to check (people and hardware)
                for category in ["people", "hardware"]:
                    # Get the value for this category from the JSON response
                    value = json_object[category]
                    
                    # Check if the value is True, handling both string "true" and boolean True
                    is_true = (isinstance(value, str) and value.lower() == "true") or (
                        isinstance(value, bool) and value is True
                    )
                    
                    # If the value is True, add the current filename to that category's list
                    if is_true:
                        result_data[category].append(filename)
                
        logger.info(f"Result data: {result_data}")
        return result_data



if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    base_path = "./documents/pliki_z_fabryki"
    suffix = ".txt"
    model_name = "gemini-2.0-flash"

    classification = Classification(logger)
    result = classification.ask_question(client, base_path, suffix, model_name)
    print(result)
