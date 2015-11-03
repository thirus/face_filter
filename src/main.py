from face_rec import FaceRec
import os
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s train_images/ src_path_to_filter/" % (sys.argv[0]))
        exit(1)
    training_images_path = sys.argv[1]
    src_images_path = sys.argv[2]

    try:
        print("Starting....")
        rec = FaceRec(training_images_path, src_images_path)
        filtered_images = rec.filter()
        print(filtered_images)
    except Exception as error:
        print(error)

    exit(0)
