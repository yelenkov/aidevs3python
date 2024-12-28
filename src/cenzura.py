import os
import sys
from dotenv import load_dotenv
import structlog
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google import genai
from google.genai import types
from config.logger import setup_logging
from config.utils import send_answer, download_file

from config.logger import setup_logging

load_dotenv()

setup_logging()
logger = structlog.get_logger(__name__)
logger.info("Starting the script")

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')
download_directory = "downloads"
filename = "cenzura.txt"
filepath = os.path.join(download_directory, filename)

# Create the downloads directory if it doesn't exist
os.makedirs(download_directory, exist_ok=True)

# Construct the download URL using the API key
download_url = f"https://centrala.ag3nts.org/data/{AIDEVS_API_KEY}/{filename}"

# Download the file
if download_file(download_url, filepath, overwrite=True):
    try:
        logger.info(f"Reading content from: {filepath}")
        with open(filepath, 'r') as f:
            content = f.read()
        logger.info(f"Successfully read {len(content)} characters from {filepath}")
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        content = None
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        content = None
else:
    logger.warning("Skipping redaction due to download failure.")
    content = None
print(content)
if content:
    system_message = """Replace all sensitive data (full names, street names + numbers, cities, person's age) with the word CENZURA.
    Maintain all punctuation, spaces, etc. Do not rephrase or add anything to the text. The full name and street name should be replaced with the word CENZURA."""

    try:
        logger.info("Sending content to Gemini API for redaction.")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_message
            )
        )
        logger.info("Received response from Gemini API.")
        stripped_response = response.text.strip()
        logger.info(stripped_response)
    except Exception as e:
        logger.error(f"Error communicating with Gemini API: {e}")
        response = None

if __name__ == "__main__":
    task = "CENZURA"
    if response:
        try:
            logger.info(f"Sending answer for task '{task}' to AIDEV's API.")
            print(stripped_response)
            send_answer(task, AIDEVS_API_KEY, stripped_response)
            logger.info("Answer sent successfully.")
        except Exception as e:
            logger.error(f"Error sending answer to AIDEV's API: {e}")
    else:
        logger.warning("No response from Gemini, skipping send_answer.")
    logger.info("Script finished.")
    