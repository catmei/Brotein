import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import glob
from io import BytesIO

class FoodRecognition:
    def __init__(self, image_bytes):
        # Load environment variables from .env file
        load_dotenv()
        # Configure the API key
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Generation configuration
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        
        # Create BytesIO object from image bytes
        self.image_buffer = BytesIO(image_bytes)
        
        # Upload the image bytes to Gemini
        self.file = genai.upload_file(self.image_buffer, mime_type="image/jpeg")
        
        # Open image from bytes for dimensions
        self.image = Image.open(BytesIO(image_bytes))
        self.pixel = self.image.size

    def upload_to_gemini(self, path, mime_type=None):
        """Uploads the given file to Gemini."""
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file

    def get_food_list(self):
        """Get the list of food items from the image using Gemini."""
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            system_instruction="Analyze the provided image of a meal. Return a Python list of the food items, grouping together items that appear to be prepared and served as a single dish.",
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        self.file,
                    ],
                },
            ]
        )

        response = chat_session.send_message("run")
        return response.text

    def get_food_list_with_nutrition(self):
        """Get the food items with their nutrition information"""
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            system_instruction="""Analyze the provided image of a meal. Group together items that appear to be prepared and served as a single dish and return the json foramt:  
            [
                {
                    "label": "food_name",
                    "nutrition": {
                        "Calories": number,
                        "Fat": number,
                        "Protein": number,
                        "Carbs": number
                    }
                }
            ]"""
        )

        chat_session = model.start_chat(history=[{"role": "user", "parts": [self.file]}])
        response = chat_session.send_message("run")
        return json.loads(response.text)

    def get_bounding_boxes(self, food_list):
        """Get the bounding boxes for the food items in the image."""
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            system_instruction="""
                Return a bounding box for the list input. \n {
                "food_name1": [ymin, xmin, ymax, xmax], 
                "food_name2": [ymin, xmin, ymax, xmax], 
                ...
            }""",
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        self.file,
                        str(food_list),
                    ],
                },
            ]
        )

        response = chat_session.send_message("run")
        return json.loads(response.text)

    def plot_boxes_and_annotations(self, image_path, annotations):
        """Plot the bounding boxes and annotations on the image."""
        try:
            image = Image.open(image_path)
        except IOError:
            print(f"Unable to open image file: {image_path}")
            return

        draw = ImageDraw.Draw(image)
        # Use a default font if no font file is found
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            font = ImageFont.load_default()

        image_width, image_height = image.size

        for food_name, bbox in annotations.items():
            ymin, xmin, ymax, xmax = map(int, bbox)
            xmin = (xmin / 1000) * image_width
            xmax = (xmax / 1000) * image_width
            ymin = (ymin / 1000) * image_height
            ymax = (ymax / 1000) * image_height
            draw.rectangle(((xmin, ymin), (xmax, ymax)), outline="red", width=2)
            draw.text((xmin, ymin - 20), food_name, fill="red", font=font)  # Adjust position as needed

        image.show()  # open the annotated image
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        result_image_path = os.path.join(os.path.dirname(image_path), f"{name}_result{ext}")
        image.save(result_image_path)
        print(f"Annotated image saved as: {result_image_path}")

# Example usage
if __name__ == "__main__":
    # Read all the image files in the test_food_set directory
    image_files = glob.glob("backend/seg/test_food_set/*.jpg")

    for image_path in image_files[2:]:
        print(f"Processing image: {image_path}")
        fr = FoodRecognition(image_path)
        food_list = fr.get_food_list()
        print("Food List:", food_list)
        annotations = fr.get_bounding_boxes(food_list)
        print("Bounding Boxes:", annotations)
        fr.plot_boxes_and_annotations(image_path, annotations)
        print("----------------------------------------------------")