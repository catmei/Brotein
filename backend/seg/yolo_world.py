from ultralytics import YOLO

# Initialize a YOLO-World model
model = YOLO("yolov8x-worldv2.pt")

# Define custom classes
model.set_classes(["person dressing white T-shirt"])

# Execute prediction for specified categories on an image
results = model.predict("traffic.jpg")

# Show results
results[0].show()