import os
from dotenv import load_dotenv
import requests
import logging
import structlog
from config.logger import setup_logging
from bs4 import BeautifulSoup
from openai import OpenAI

load_dotenv()

setup_logging()
logger = structlog.get_logger(__name__)

def solve_captcha(question):
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides precise, numeric answers to historical questions."},
            {"role": "user", "content": f"What is the numeric answer to this question: {question}? Respond ONLY with the number."}
        ],
        max_tokens=10,
        temperature=0.2  # Low temperature for more precise answers
    )
    
    answer = response.choices[0].message.content.strip()

    return int(answer)


def login():
    url = 'https://xyz.ag3nts.org/'
    
    session = requests.Session()
    
    response = session.get(url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Dynamically extract the captcha question
    captcha_question_element = soup.find('p', id='human-question')
    if captcha_question_element:
        captcha_question = captcha_question_element.text.replace('Question:\n', '').strip()
    else:
        print("Captcha question not found")
        return None
    
    captcha_answer = solve_captcha(captcha_question)
    
    login_payload = {
        'username': 'tester',
        'password': '574e112a',
        'answer': captcha_answer
    }
    
    login_response = session.post(url, data=login_payload)
    
    print(f"login_response: \n\n {login_response.text}")
    
    return login_response

def download_specific_files():
    files_to_download = [
        '/files/0_13_4b.txt', # flaga
        '/files/0_13_4.txt', # flaga
        '/files/0_12.1.txt' # there is no such file
    ]
    
    base_url = 'https://xyz.ag3nts.org'
    
    # Create downloads directory if it doesn't exist
    import os
    os.makedirs('downloads', exist_ok=True)
    
    for file_path in files_to_download:
        # Construct full URL
        full_url = f'{base_url}{file_path}'
        
        try:
            # Download the file
            response = requests.get(full_url)
            
            # Check if the response is successful
            if response.status_code == 200:
                # Create filename
                filename = os.path.basename(file_path)
                filepath = os.path.join('downloads', filename)
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Downloaded: {filename}")
                print(f"Content: {response.text}")
            else:
                print(f"Failed to download {file_path}. Status code: {response.status_code}")
        
        except Exception as e:
            print(f"Error downloading {file_path}: {e}")

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the script")
    login()
    download_specific_files()