from ultralytics.data.annotator import auto_annotate

auto_annotate(data="S__7069700.jpg", det_model="yolo11x.pt", sam_model="sam2_b.pt")