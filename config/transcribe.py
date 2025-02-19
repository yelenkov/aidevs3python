import os
import sys
from dotenv import load_dotenv
import structlog
from google import genai

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
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

    def transcribe_single_audio(self, client, file_path: str, model_name: str, save_output: bool = False) -> str:
        """
        Transcribes a single audio file.

        Args:
            client: The Gemini API client.
            file_path (str): The full path to the audio file.
            model_name (str): The name of the Gemini model to use for transcription.
            save_output (bool, optional): Whether to save the transcription to a text file. Defaults to False.

        Returns:
            str: The transcribed text, or an error message if transcription fails.
        """
        logger = self.logger
        logger.info("Starting transcription for a single audio file")
        logger.info(f"Model name: {model_name}, File path: {file_path}, Save output: {save_output}")

        try:
            object = os.path.basename(file_path)
            file = client.files.upload(file=file_path, config={'display_name': object})
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
                txt_file_path = os.path.join(os.path.dirname(file_path), f"{object.split('.')[0]}.txt")
                with open(f'{txt_file_path}', 'w') as f:
                    f.write(response.text)
                logger.info(f"Transcription saved to: {txt_file_path}")
            else:
                logger.info(f"Transcription Text:\n{response.text}")

            logger.info("Transcription complete for single audio file.")
            return response.text
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return f"Error during transcription: {e}"

    def transcribe_audio_directory(self, client, base_path: str, suffix: str, model_name: str, save_output: bool = False) -> dict:
        """
        Processes all audio files in a given directory for transcription.

        Args:
            client: The Gemini API client.
            base_path (str): The path to the directory containing audio files.
            suffix (str): The suffix of the audio files to process (e.g., '.mp3').
            model_name (str): The name of the Gemini model to use for transcription.
            save_output (bool, optional): Whether to save transcriptions to text files. Defaults to False.

        Returns:
            dict: A dictionary containing transcription results for each processed audio file,
                  with filenames as keys and transcription text as values.
        """
        logger = self.logger
        logger.info("Starting to process audio files in directory.")
        logger.info(f"Base path: {base_path}, Suffix: {suffix}, Model name: {model_name}, Save output: {save_output}")
        transcription_dictionary_output = {} # Initialize dictionary to store results

        for filename in os.listdir(base_path):
            if filename.endswith(suffix):
                file_path = os.path.join(base_path, filename)
                logger.info(f"Processing audio file: {filename}, file_path: {file_path}")
                transcription_result = self.transcribe_single_audio(client, file_path, model_name, save_output) # Transcribe single file
                transcription_dictionary_output[filename] = transcription_result # Store result

        logger.info("Audio directory processing complete.")
        return transcription_dictionary_output

if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    logger.info("Starting the script")

    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model_name = "gemini-2.0-flash"
    base_path = "./documents/pliki_z_fabryki"
    suffix = ".mp3"
    transcriber = AudioTranscriber(logger)

    transcriber.transcribe_audio_directory(client, base_path, suffix, model_name, save_output=True)