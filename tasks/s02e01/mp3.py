import os
import sys
from dotenv import load_dotenv
import structlog

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google import genai
from google.genai import types
from config.utils import send_answer, transcribe_audio
from config.logger import setup_logging
load_dotenv()

setup_logging()

logger = structlog.get_logger(__name__)
logger.info("Starting the script")

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

input_dir = "./documents/przesluchania"
output_dir = "./downloads/audio"

logger.info("Processing files in {input_dir}", input_dir=input_dir)

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

logger.info("Finished processing files.")

system_instruction = "Odpowiedz zwięźle na pytanie: na jakiej ulicy znajduje się uczelnia, na której wykłada Andrzej Maj?"

all_transcribed_text = []

# Read the content of each transcribed file
for filename in os.listdir(output_dir):
    if filename.endswith('.txt'):
        filepath = os.path.join(output_dir, filename)
        logger.info("Reading transcribed file: {filepath}", filepath=filepath)
        try:
            with open(filepath, 'r') as f:
                transcribed_text = f.read()
                all_transcribed_text.append(transcribed_text)
        except Exception as e:
            logger.error("Error reading file {filepath}: {error}", filepath=filepath, error=str(e))

# Join all the transcribed text together
combined_transcribed_text = "\n".join(all_transcribed_text)
logger.info("Combined transcribed text {combined_transcribed_text}", combined_transcribed_text=combined_transcribed_text)

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        ),
        contents=[combined_transcribed_text] # Send the combined text
    )
    logger.info("Gemini response: {response}", response=response.candidates[0].content.parts[0].text)
    send_answer("MP3", AIDEVS_API_KEY, response.candidates[0].content.parts[0].text) # Send the text response

except Exception as e:
    logger.error("Error generating content with Gemini: {error}", error=str(e))

logger.info("Finished processing transcribed files.")