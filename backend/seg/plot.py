import json
import cv2


# Function to draw the image with bounding boxes and annotations using OpenCV
def draw_bounding_boxes(image_path, annotation_data, output_path):
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Image not found at {image_path}")
        return

    # Iterate over the annotations and draw each bounding box and label
    for annotation in annotation_data["annotations"]:
        # Get the bounding box coordinates and color
        bbox = annotation["bbox"]
        color = tuple(annotation["color"])  # Convert list to tuple

        # Draw the bounding box
        cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

        # Adjust label position to be a little above the top-left corner
        label_x = bbox[0] + 15
        label_y = max(bbox[1] - 15, 0)  # Ensure the label is not outside the image

        # Add label text
        cv2.putText(image, annotation["label"], (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    # Save the annotated image using OpenCV
    cv2.imwrite(output_path, image)


# Load the annotation data from the JSON file
annotation_file_path = "01.json"  # Make sure the file path is correct
with open(annotation_file_path, "r") as f:
    annotation_data = json.load(f)

# Image path
image_path = "S__7069700.jpg"  # Make sure the image file path is correct

# Generate the output file name by replacing .json with .png
output_file_path = annotation_file_path.replace('.json', '.jpg')

# Call the function to draw bounding boxes and save the image
draw_bounding_boxes(image_path, annotation_data, output_file_path)

print(f"Annotated image saved as {output_file_path}")
