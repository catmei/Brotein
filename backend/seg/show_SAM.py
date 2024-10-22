import matplotlib.pyplot as plt
from PIL import Image

# Load image
image_path = "S__7069700.jpg"
image = Image.open(image_path)
image_width, image_height = image.size

# Load annotations from the .txt file
annotations_file = "S__7069700_auto_annotate_labels/S__7069700.txt"
annotations = []
with open(annotations_file, 'r') as file:
    for line in file:
        # Each line in the format: class x_center y_center width height (normalized values)
        values = list(map(float, line.strip().split()))
        annotations.append(values)

# Plot the image
plt.imshow(image)
ax = plt.gca()

# Loop over each annotation and plot the bounding boxes
for annotation in annotations:
    class_id, x_center_norm, y_center_norm, width_norm, height_norm = annotation[:5]

    # Convert normalized coordinates to absolute pixel values
    x_center = x_center_norm * image_width
    y_center = y_center_norm * image_height
    width = width_norm * image_width
    height = height_norm * image_height

    # Calculate the top-left corner of the bounding box
    x_min = x_center - width / 2
    y_min = y_center - height / 2

    # Create a rectangle patch for the bounding box
    rect = plt.Rectangle((x_min, y_min), width, height, edgecolor='red', facecolor='none', linewidth=2)
    ax.add_patch(rect)

# Show the plot with bounding boxes
plt.axis('off')
plt.show()
