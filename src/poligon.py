import os
import sys
from dotenv import load_dotenv
import requests
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logger import setup_logging
load_dotenv()

def poligon(task:str):
    # Fetch data from the text file
    response = requests.get('https://poligon.aidevs.pl/dane.txt')
    # Split the content into a list of strings by newline
    data_array = response.text.strip().split('\n')
    # Prepare the payload
    payload = {
        "task": task,
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": data_array
    }
    # Send POST request to verify endpoint
    verify_response = requests.post('https://poligon.aidevs.pl/verify', json=payload)
    # Print the response
    print(verify_response.json())

if __name__ == "__main__":
    task = "POLIGON"
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the script")
    poligon(task)