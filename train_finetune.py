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

# from ultralytics import YOLO

# # Load the trained model
# model = YOLO()

# # Validate accuracy on dataset
# results = model.val(data=r"C:\Users\jy\Desktop\Capstone project\combined_dataset\data.yaml")

# print(results)
from ultralytics import YOLO

if __name__ == "__main__":

    # Load pretrained YOLOv8 model (COCO)
    pretrained_model = YOLO(r"C:\Users\jy\Desktop\Capstone project\runs\detect\train_dataset_finetune\weights\best.pt")

    # Quantitative evaluation on your dataset
    pretrained_results = pretrained_model.val(
        data=r"C:\Users\jy\Desktop\Capstone project\combined_dataset\data.yaml",
        imgsz=720,      # SAME image size
        conf=0.5,       # SAME confidence threshold
        iou=0.7,        # SAME IoU threshold
        plots=True,     # generate PR curves & confusion matrix
        save=True
    )

    print(pretrained_results)
