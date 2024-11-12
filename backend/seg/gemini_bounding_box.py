import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variables
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction="""
    Return a bounding box for the list input. \n {
    "food_name1": [ymin, xmin, ymax, xmax], 
    "food_name2": [ymin, xmin, ymax, xmax], 
    ...
  }""",
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini("backend/seg/S__7069700.jpg", mime_type="image/jpeg"),
]

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        files[0],
        "[\"pan-fried salmon\", \"steamed sweet potatoes\", \"creamy mushroom and corn dish\"]",
      ],
    },
  ]
)

response = chat_session.send_message("run")

print(response.text)