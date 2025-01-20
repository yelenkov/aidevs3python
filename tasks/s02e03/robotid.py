import os
import sys
from dotenv import load_dotenv
import structlog
import requests
from google import genai
from google.genai import types

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from config.logger import setup_logging
from config.utils import send_answer
load_dotenv()

def main():
    setup_logging()
    logger = structlog.get_logger(__name__)
    logger.info("Starting the script")

    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

    data = f"https://centrala.ag3nts.org/data/{AIDEVS_API_KEY}/robotid.json"

    response = requests.get(data)

    description = response.json()['description']
    print(description)

    url = "https://storage.googleapis.com/starset-random/unnamed.png"
    answer = send_answer("robotid", AIDEVS_API_KEY, url)
    print(answer)

if __name__ == "__main__":
    main()