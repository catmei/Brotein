from ultralytics.data.annotator import auto_annotate

results = auto_annotate(data="S__7069700.jpg", det_model="yolov8x.pt", sam_model="sam2_b.pt")

# Visualize the results
for i, r in enumerate(results):
    # Show results to screen (in supported environments)
    r.show()

    # Save results to disk
    r.save(filename=f"results{i}_sam__annotation.jpg")