# from ultralytics import YOLO

# if __name__ == "__main__":
#     from multiprocessing import freeze_support
#     freeze_support()  # needed for Windows

#     model = YOLO(r"C:\Users\jy\Desktop\Capstone project\runs\detect\train_dataset1\weights\best.pt")

#     model.train(
#         data=r"C:\Users\jy\Desktop\Capstone project\combined_dataset\data.yaml",
#         epochs=100,
#         batch=16,
#         imgsz=720,
#         name="train_dataset_finetune"
#     )

from ultralytics import YOLO

# Load the trained model
model = YOLO(r"C:\Users\jy\Desktop\Capstone project\runs\detect\train_dataset_finetune\weights\best.pt")

# Validate accuracy on dataset
results = model.val(data=r"C:\Users\jy\Desktop\Capstone project\combined_dataset\data.yaml")

print(results)