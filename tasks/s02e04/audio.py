import os
import structlog
import google.generativeai as genai
import tenacity

from config.logger import setup_logging

class AudioProcessor:
    """
    A class to handle audio processing.
    """
    def __init__(self, logger):
        """
        Initializes the AudioProcessor with an optional logger.
        """
        self.logger = logger if logger else structlog.get_logger(__name__) # Use provided logger or create a default

    @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2)) # Retry 3 times, wait 2 seconds between retries
    def _get_audio_response(self, model, prompt, audio_file):
        """
        Helper function with retry logic
        """
        response = model.generate_content([prompt, audio_file])
        response.resolve()
        return response.text

    def transcribe_audio(self, base_path: str, suffix: str, model_name: str, save_output: bool = False) -> dict:
        audio_file = genai.upload_file(base_path, suffix)

        prompt = "Generate a transcript of the speech."
        model = genai.GenerativeModel(model_name=model_name)
        result = model.generate_content([prompt, audio_file])

    def transcribe_audio(client, input_file_path: str, output_file_path: str, model_name: str):
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
                model=model_name,
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


        # Process each file in the input directory
        for filename in os.listdir(input_dir):
            if filename.endswith('.m4a'):  # Only process m4a files
                input_filepath = os.path.join(input_dir, filename)
                output_filename = os.path.splitext(filename)[0] + ".txt"
                output_filepath = os.path.join(output_dir, output_filename)

                if os.path.exists(output_filepath):
                    logger.info("Output file already exists for {input_filepath}. Skipping.", input_filepath=input_filepath)
                else:
                    transcribe_audio(client, input_filepath, output_filepath)

if __name__ == "__main__":
    setup_logging()
    logger = structlog.get_logger(__name__)
    audio_processor = AudioProcessor(logger)

    base_path = "/home/xbloc/Respos/aidevs3python/documents/pliki_z_fabryki"
    suffix = ".mp3"
    model_name = "gemini-2.0-flash-exp"

    audio_processor.transcribe_audio(base_path, suffix, model_name, save_output=False)
