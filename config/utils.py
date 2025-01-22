import os
import sys
from dotenv import load_dotenv
import requests
import structlog
import pathlib
import logging
from google.genai import types
from config.logger import setup_logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

logger = structlog.get_logger(__name__)

def send_answer(task:str, apikey:str, answer:str):

    url = "https://centrala.ag3nts.org/report"

    payload = {
        "task": task,
        "apikey": apikey,
        "answer": answer
    }

    logger.info(f"Sending answer for task '{payload}' to AIDEV's API.")
    verify_response = requests.post(url, json=payload)
    print(verify_response.json())

def download_file(url, filepath, overwrite=False):
    """Downloads a file from the given URL and saves it to the specified filepath.

    Args:
        url (str): The URL to download the file from.
        filepath (str): The path to save the downloaded file to.
        overwrite (bool, optional): Whether to overwrite the file if it exists. Defaults to False.
    """
    if os.path.exists(filepath) and not overwrite:
        logger.warning(f"File already exists at {filepath} and overwrite is set to False. Skipping download.")
        return True  # Treat as successful as the file exists

    logger.info(f"Downloading file from: {url} to {filepath}, overwrite={overwrite}")
    file_mode = 'wb'
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(filepath, file_mode) as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"Successfully downloaded file to: {filepath}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file from {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error writing file to {filepath}: {e}")
        return False
        
def transcribe_audio(client, input_file_path, output_file_path):
    logger.info("Transcribing {input_file_path}", input_file_path=input_file_path)
    try:
        with open(input_file_path, 'rb') as audio_file:
            audio_content = audio_file.read()

        if not audio_content:  # Check if the file content is empty
            logger.warning("Skipping empty file: {input_file_path}", input_file_path=input_file_path)
            return  # Skip processing this file

        audio_path = pathlib.Path(input_file_path)
        audio_path.write_bytes(audio_content)

        file_upload = client.files.upload(path=audio_path)

        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=file_upload.uri, 
                            mime_type=file_upload.mime_type
                        )
                    ]
                ),
                "Transcribe the following audio file",
            ]
        )
        logger.info("Transcription response", response_text=response.candidates[-1].content.parts[0].text)

        with open(output_file_path, 'w') as text_file:
            text_file.write(response.text)
        logger.info("Transcription saved to {output_file_path}", output_file_path=output_file_path)
    except Exception as e:
        logger.error("Error transcribing {input_file_path}", input_file_path=input_file_path, error=str(e))