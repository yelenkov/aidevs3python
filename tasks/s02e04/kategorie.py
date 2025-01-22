import os
import sys
from dotenv import load_dotenv
import structlog
import requests
import google.generativeai as genai
from google.genai import types
import PIL.Image
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from config.logger import setup_logging
load_dotenv()

def main():
    # Initialize logging
    setup_logging()  # Call the setup_logging function
    logger = structlog.get_logger(__name__)
    logger.info("Starting image analysis")

    result_data = {
        "people": [],
        "hardware": [],
        "other": [] # Add 'other' category
    }

    # Configure the Gemini API client
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    system_prompt = create_prompt()

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=system_prompt,
    )

    # Get base path
    base_path = "/home/xbloc/Respos/aidevs3python/documents/pliki_z_fabryki"

    # Load images with filenames
    images_with_names = load_images(base_path)

    logger.info(f"Processing {len(images_with_names)} images...")

    # Process each image individually
    for filename, image in images_with_names:
        logger.info(f"Sending request to Gemini for image: {filename}")
        try:
            response = model.generate_content([system_prompt, image])
            response.resolve() # Ensure response is resolved before accessing text

            raw_response_text = response.text
            logger.info(f"Raw response from Gemini: {raw_response_text}")

            try:
                response_json = json.loads(raw_response_text) # Parse JSON response
                category = response_json.get("category")

                if category in result_data: # Check if category is valid
                    result_data[category].append(filename)
                    logger.info(f"Image '{filename}' categorized as '{category}'")
                else:
                    result_data["other"].append(filename) # Default to 'other' if category is unexpected
                    logger.warning(f"Unexpected category '{category}' in response for image '{filename}'. Categorized as 'other'.")
    
            except json.JSONDecodeError:
                result_data["other"].append(filename) # Treat as 'other' if JSON parsing fails
                logger.error(f"Failed to decode JSON response for image '{filename}'. Raw response: '{raw_response_text}'. Categorized as 'other'.")
            except AttributeError as e:
                result_data["other"].append(filename) # Handle potential AttributeError if response.text is None
                logger.error(f"AttributeError processing response for image '{filename}': {e}. Raw response: '{raw_response_text}'. Categorized as 'other'.")


        except Exception as e: # Catch any potential errors during API call or processing
            result_data["other"].append(filename) # Categorize as 'other' in case of error
            logger.error(f"Error processing image '{filename}': {e}")


    print("\nImage Analysis Results:")
    print(json.dumps(result_data, indent=2)) # Print final JSON result
    logger.info("Analysis complete")

if __name__ == "__main__":
    main()