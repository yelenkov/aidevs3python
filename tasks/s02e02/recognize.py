import os
import sys
import structlog
import PIL.Image
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from config.logger import setup_logging
load_dotenv()

def load_images(base_path: str) -> list[PIL.Image.Image]:
    """Loads map images from the resources directory."""
    image_paths = [
        os.path.join(base_path, "resources", f"map{i}.png") for i in range(1, 5)
    ]
    images = [PIL.Image.open(path) for path in image_paths]
    return images

def create_prompt() -> str:
    """Creates the prompt for the Gemini model."""
    prompt = """You're going to receive 4 map fragments.
                    Three of them are from the same city.
                    Write the name of the streets that are present on map.
                    Write the name of the city in Polish.
                    We are looking for city that had granaries and fortress.
                    Please explain your way of thinking.
                    Double check if city you're going to give me as answer has locations presented in the map fragments.
                    Finally write only the name of the city.
                    Your response should be:
                    <NAME_OF_THE_CITY>"""
    return prompt

def main():
    # Initialize logging
    setup_logging()  # Call the setup_logging function
    logger = structlog.get_logger(__name__)
    logger.info("Starting image analysis")

    try:
        # Configure the Gemini API client
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-thinking-exp",
            system_instruction="You are an expert in image analysis. With specialization on maps analysis",
        )

        # Get base path
        base_path = os.getcwd()

        # Load images
        images = load_images(base_path)

        # Create prompt
        prompt = create_prompt()

        logger.info("Sending request to Gemini")
        # Generate content with the model
        response = model.generate_content([prompt] + images)

        print("\nImage Analysis Results:")
        print(f"{response.text}")
        logger.info("Analysis complete")

    except Exception as e:
        logger.error("An error occurred during image analysis", error=str(e))
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()