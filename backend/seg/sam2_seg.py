from PIL import Image
from ultralytics import SAM

# Load a model
model = SAM("sam2_t.pt")

# Display model information (optional)
model.info()

# Run inference
results = model("S__7282709.jpg")


# Visualize the results
for i, r in enumerate(results):
    # Plot results image
    im_bgr = r.plot()  # BGR-order numpy array
    im_rgb = Image.fromarray(im_bgr[..., ::-1])  # RGB-order PIL image

    # Show results to screen (in supported environments)
    r.show()

    # Save results to disk
    r.save(filename=f"results{i}_sam.jpg")