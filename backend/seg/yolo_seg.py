from PIL import Image

from ultralytics import YOLO

# Load a pretrained YOLO11n model
model = YOLO("yolo11x-seg.pt")

# Run inference on 'bus.jpg'
results = model(["S__7282709.jpg"])  # results list

# Visualize the results
for i, r in enumerate(results):
    # Plot results image
    im_bgr = r.plot()  # BGR-order numpy array
    im_rgb = Image.fromarray(im_bgr[..., ::-1])  # RGB-order PIL image

    # Show results to screen (in supported environments)
    r.show()

    # Save results to disk
    r.save(filename=f"results{i}_seg.jpg")