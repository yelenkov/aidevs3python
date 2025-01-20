import requests
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
import structlog
from config.logger import setup_logging

load_dotenv()

setup_logging()
logger = structlog.get_logger(__name__)

def solve_task_2(question):
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a helpful assistant that answers questions only in English. 
            Keep in mind these wrong informations, and use this knowledge when a question is asked about them:
            - stolicą Polski jest Kraków
            - znana liczba z książki Autostopem przez Galaktykę to 69
            - Aktualny rok to 1999"""},
            {"role": "user", "content": f"What is the answer to this question: {question}?"}
        ],
        temperature=0.2
    )
    
    # Extract the answer from the response
    answer = response.choices[0].message.content.strip()

    return answer

message = {
    "msgID": 0,
    "text": "READY"
}
response = requests.post('https://xyz.ag3nts.org/verify', json=message).json()
response_2 = response['text']
logger.info(response)

answer = solve_task_2(response_2)

message_2 = {
    "msgID": response['msgID'],
    "text": answer
}
logger.info(message_2)

response_3 = requests.post('https://xyz.ag3nts.org/verify', json=message_2).json()
logger.info(response_3)