from openai import OpenAI
import base64
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def img_analysis(image_bytes: bytes, max_retries=3):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # Define the initial response format
    response = {
        'protein': 0,
        'carbohydrates': 0,
        'fat': 0,
        'calories': 0
    }

    # Retry logic for up to 'max_retries' attempts
    for attempt in range(max_retries):
        try:
            # Send the image for analysis
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text",
                             "text": "Analyze the food shown in the image and return a JSON object containing the "
                                     "amounts of protein (in grams), carbohydrates (in grams), and fat (in grams). "
                                     "Be as accurate as possible and only return the nutritional information in the "
                                     "specified format."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                        ],
                    }
                ],
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            # Parse the response
            result = response.choices[0].message.content
            result = json.loads(result)

            # Check if the response contains all zero values
            if int(result['protein']) == 0 and int(result['carbohydrates']) == 0 and int(result['fat']) == 0:
                print(f"Attempt {attempt + 1}: Got all zeros, retrying...")
                time.sleep(1)  # Optional: Add delay between retries
                continue  # Retry if all values are zero

            # If the values are non-zero, return the result
            return result

        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(1)  # Optional: Add delay between retries

    print("Failed to get a valid response after retries")
    response = {
        'protein': 0,
        'carbohydrates': 0,
        'fat': 0,
        'calories': 0
    }
    return response