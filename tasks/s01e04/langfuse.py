import sys
import os
from langfuse.openai import openai
from dotenv import load_dotenv
import logging
from tasks.s01e04.langfuse import Langfuse

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

langfuse = Langfuse(
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    host=os.getenv('LANGFUSE_HOST')
)

chat_completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello!"}]
)

logger.info(f"ChatGPT response: {chat_completion.choices[0].message.content}")

if __name__ == "__main__":
    auth_response = langfuse.auth_check()
    logger.info(f"Langfuse auth check: {auth_response}")