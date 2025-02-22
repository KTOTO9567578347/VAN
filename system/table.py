import ultralytics
model = ultralytics.YOLO("./models/classify_face.pt")
print(model.names)