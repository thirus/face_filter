import cv2
import sys
import os
import numpy

class FaceRec(object):
    SUPPORTED_IMAGE_EXTN = ['.jpg', '.png', '.pgm', '.jpeg', '.gif']

    def __init__(self, training_images_path, src_images_path, face_haar_cascase_xml_file="/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml"):
        self.training_images_path = training_images_path
        self.src_images_path = src_images_path
        self.face_cascade = cv2.CascadeClassifier(face_haar_cascase_xml_file)

    def filter(self):
        result_images = []
        print("Training images..")
        model = self.get_face_rec_model()

        filenames = next(os.walk(self.src_images_path))[2]

        for name in self.filter_pictures(filenames):
            img_path = os.path.join(self.src_images_path, name)
            subject_faces = self.get_subject_faces(img_path)

            if len(subject_faces) == 0:
                print("Subject face not found in %s" % img_path)
                continue

            print("Found %s faces for %s" % (len(subject_faces), img_path))
            self.save_subject_faces(subject_faces, name)
            for subject_face_img in subject_faces:
                # cv2.imshow("face", subject_face_img)
                # cv2.waitKey(0)
                # model.setThreshold(0.0)
                predict_label, confidence = model.predict(subject_face_img)
                result_images.append((img_path, predict_label, confidence))

        return result_images

    def filter_pictures(self, files):
        return [pfile for pfile in files if os.path.splitext(pfile)[1] in FaceRec.SUPPORTED_IMAGE_EXTN]

    def get_subject_faces(self, filename):
        subject_img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        subject_faces = self.find_faces(subject_img)
        return subject_faces

    def save_subject_faces(self, faces, basename):
        out_path = os.path.join(self.src_images_path, 'output')
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        i = 0
        for face in faces:
            name = str(i) + basename
            out_filename = os.path.join(out_path, name)
            cv2.imwrite(out_filename, face)
            i += 1

    def find_faces(self, img):
        face_images = []
        faces = self.face_cascade.detectMultiScale(img, 1.3, 5)

        if len(faces) == 0:
            return face_images

        for (x,y,w,h) in faces:
            face_img = img[y:y+h, x:x+w]
            face_images.append(face_img)

        return face_images

    def process_training_images(self, images_path):
        i = 0
        train_images = []
        labels = []
        normalized_images_path = os.path.join(images_path, 'normalized')
        if not os.path.exists(normalized_images_path):
            os.mkdir(normalized_images_path)

        filenames = next(os.walk(images_path))[2]

        for name in self.filter_pictures(filenames):
            img_path = os.path.join(images_path, name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            img = cv2.equalizeHist(img)

            faces = self.find_faces(img)

            if len(faces) > 0:
                face_img = faces[0]
                train_images.append(img)
                labels.append(i)
                i += 1
                out_filename = os.path.join(normalized_images_path, name)
                cv2.imwrite(out_filename, face_img)
        return train_images, labels

    def get_face_rec_model(self):
        train_images, labels = self.process_training_images(self.training_images_path)

        if len(train_images) == 0:
            raise Exception("No Training images found!")

        model = cv2.face.createLBPHFaceRecognizer()
        model.train(train_images, numpy.array(labels))
        return model
