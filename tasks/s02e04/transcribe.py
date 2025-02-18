import os
import sys
from dotenv import load_dotenv
import structlog
from google import genai

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)
from config.logger import setup_logging
load_dotenv()

class AudioTranscriber:
    """
    A class to handle audio transcription.
    """
    def __init__(self, logger):
        """
        Initializes the AudioTranscriber with a logger.
        """
        self.logger = logger if logger else structlog.get_logger(__name__)

    def list_files(self, client):
        logger = self.logger
        logger.info("Starting to list files.")
        for f in client.files.list():
            logger.info(f'File: {f.name}')
        logger.info("Finished listing files.")

    def delete_files(self, client):
        logger = self.logger
        logger.info("Starting to delete files.")
        for f in client.files.list():
            logger.info(f'Deleting file: {f.name}')
            client.files.delete(name=f.name)
        logger.info("Finished deleting files.")

    def upload_files(self, client, base_path: str, suffix: str):
        logger = self.logger
        logger.info(f"Starting to upload files from path: {base_path} with suffix: {suffix}")
        for file in os.listdir(base_path):
            if file.endswith(suffix):
                logger.info(f'Uploading file: {file}')
                client.files.upload(file=base_path + '/' + file, config={'display_name': file})
        logger.info("Finished uploading files.")

    def transcribe_audio(self, client, base_path: str, suffix: str, model_name: str, save_output: bool = True):
        logger = self.logger
        logger.info("Transcribing audio files")
        logger.info(f"Model name: {model_name}, Base path: {base_path}, Suffix: {suffix}, Save output: {save_output}")

        for object in os.listdir(base_path):
            if object.endswith(suffix):
                file = client.files.upload(file=base_path + '/' + object, config={'display_name': object})
                logger.info(f'Uploaded file: {object}')
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                    "Transcribe the following audio file, do not include any other information, just the text.",
                    file,
                ]
            )
                logger.info(f'Transcription response: {response.text}')

                if save_output:
                    txt_file_path = os.path.join(base_path, f"{object.split('.')[0]}.txt")
                    with open(f'{txt_file_path}', 'w') as f:
                        f.write(response.text)
        logger.info("Finished transcribing audio files.")

if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    logger.info("Starting the script")

    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model_name = "gemini-2.0-flash"
    base_path = "./documents/pliki_z_fabryki"
    suffix = ".mp3"
    transcriber = AudioTranscriber(logger)

    transcriber.transcribe_audio(client, base_path, suffix, model_name, save_output=True)