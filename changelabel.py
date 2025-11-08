import os
import shutil

# Target folder (where merged dataset will be created)
target_base = r"C:\Users\jy\Desktop\Capstone project\combined_dataset"

# Source datasets
person_train_images = r"C:\Users\jy\Downloads\person\person\person-3\train\images"
person_train_labels = r"C:\Users\jy\Downloads\person\person\person-3\train\labels"
person_valid_images = r"C:\Users\jy\Downloads\person\person\person-3\valid\images"
person_valid_labels = r"C:\Users\jy\Downloads\person\person\person-3\valid\labels"

car_train_images = r"C:\Users\jy\Downloads\archive\archive\car_dataset-master\train\images"
car_train_labels = r"C:\Users\jy\Downloads\archive\archive\car_dataset-master\train\labels"
car_valid_images = r"C:\Users\jy\Downloads\archive\archive\car_dataset-master\valid\images"
car_valid_labels = r"C:\Users\jy\Downloads\archive\archive\car_dataset-master\valid\labels"

# Define output folders
folders = [
    os.path.join(target_base, "train", "images"),
    os.path.join(target_base, "train", "labels"),
    os.path.join(target_base, "valid", "images"),
    os.path.join(target_base, "valid", "labels"),
]

# Create directories if not exist
for folder in folders:
    os.makedirs(folder, exist_ok=True)

def move_dataset(src_img, src_lbl, dst_img, dst_lbl, prefix):
    img_files = [f for f in os.listdir(src_img) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    for i, file in enumerate(img_files):
        # Move image
        src_image_path = os.path.join(src_img, file)
        dst_image_name = f"{prefix}_{i}_{file}"
        dst_image_path = os.path.join(dst_img, dst_image_name)
        shutil.move(src_image_path, dst_image_path)

        # Move label
        label_name = os.path.splitext(file)[0] + ".txt"
        src_label_path = os.path.join(src_lbl, label_name)
        dst_label_path = os.path.join(dst_lbl, f"{prefix}_{i}_{label_name}")
        if os.path.exists(src_label_path):
            shutil.move(src_label_path, dst_label_path)

    print(f"✅ Moved {len(img_files)} images from {src_img}")

# Merge train
move_dataset(person_train_images, person_train_labels, folders[0], folders[1], "person_train")
move_dataset(car_train_images, car_train_labels, folders[0], folders[1], "car_train")

# Merge valid
move_dataset(person_valid_images, person_valid_labels, folders[2], folders[3], "person_valid")
move_dataset(car_valid_images, car_valid_labels, folders[2], folders[3], "car_valid")

print("\n🎯 Merge complete! Combined dataset ready (files moved).")
