import cv2
import os
import firebase_admin
import pyrebase
import face_recognition
import pickle
import numpy as np
from PIL import Image
from firebase_admin import credentials
from firebase_admin import firestore
from src.utils import Patient

config={
    "apiKey": "apikey",
    "authDomain": "raspconnect-3850a.firebaseapp.com",
    "databaseURL": "dburl",
    "projectId": "raspconnect-3850a",
    "storageBucket": "raspconnect-3850a.appspot.com",
    "serviceAccount": "/home/chirag/Documents/Code_new/WatchDog_Server/src/raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json",
    "messagingSenderId": "messagingsenderid",
    "appId": "appid",
    "measurementId": "measurementID"
}

firebase=pyrebase.initialize_app(config)
storage=firebase.storage()
cred=credentials.Certificate(
    "/home/chirag/Documents/Code_new/WatchDog_Server/src/raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://raspconnect-3850a.firebaseio.com",
    "databaseAuthVariableOverride": None
})

db=firestore.client()

path_for_videos = "/home/chirag/Documents/Code_new/WatchDog_Server/media"
path_image_data = "/home/chirag/Documents/Code_new/WatchDog_Server/dataset"
path_fface_model = '/home/chirag/Documents/Code_new/WatchDog_Server/cascades/haarcascade_frontalface_alt2.xml'


def get_patient_infos():
    patient_list = []
    collection = db.collection(u"patient database")
    docs = collection.get()
    for post in docs:
        print(u'{} => {}'.format(post.id, post.to_dict()))
        data = post.to_dict()
        try: pname = data['name']
        except: pname = ""
        try: pid = data['patient_id']
        except: pid = ""
        try: rname = data['room']
        except: rname = ""
        try:
            if data['allowance'].lower() == 'yes':
                allow = True
            elif data['allowance'].lower() == 'no':
                allow = False
            else:
                allow = None
        except: allow = None
        try: vname = data['video_name']
        except: vname = ""
        try: vid = data['video_id']
        except: vid = ""

        patient = Patient(pname, pid, rname, allow, vname, vid)
        patient_list.append(patient)

    return patient_list


def download_video(patients):

    vidfiles=storage.child('/').list_files()
    db_vid_names = []
    for vid in vidfiles:db_vid_names.append(vid.name)


    for patient in patients:
        vid_fname = "videos/" + patient.video_id
        print(vid_fname)
        print("--------")
        for vid in db_vid_names :

            if str(vid) == str(vid_fname):
                target_path = path_for_videos + "/" + patient.video_id
                try:
                    storage.child(vid_fname).download(target_path)
                    patient.video_local_path = target_path
                except:
                    print("[Warning] Failed in downloading of {}.".format(patient.video_id))
                if patient.video_local_path is not None:
                    break
            else:
                print(vid)
                print(vid_fname)
    return patients


def capture_encode_faces(patients, encoding_file="encodings.pickle", detection_method='hog', skip=5, angle=270):
    face_detector=cv2.CascadeClassifier(path_fface_model)
    knownEncodings=[]
    knownNames=[]

    for patient in patients:
        if patient.video_local_path is None:
            continue

        count = 0
        capt = cv2.VideoCapture(patient.video_local_path)
        fnum = 1

        while (capt.isOpened()):

            ret, frame = capt.read()
            if not ret:
                break
            # skip frame
            # I get the frame image per 5 frames. ex: 1 image per about 0.5~1 second in the video file.ok
            if fnum % skip > 0:
                fnum += 1
                continue
            else:
                fnum = 1
            # rotate image
            im=Image.fromarray(frame)
            out=im.rotate(angle, expand=True)
            frame=np.array(out)

            # face detect
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                face=gray[y:y+h, x:x+w]
                cv2.rectangle(gray, (x, y), (x+w, y+h), (255, 0, 0), 2)

                # face recognize and encoding.
                face = cv2.cvtColor(face, cv2.COLOR_GRAY2RGB)

                boxes=face_recognition.face_locations(face, model=detection_method)
                # compute the facial embedding for the face
                encodings=face_recognition.face_encodings(face, boxes)
                # loop over the encodings
                for encoding in encodings:
                    # add each encoding + name to our set of known names and
                    # encodings
                    knownEncodings.append(encoding)
                    knownNames.append(patient.patient_name)
                count += 1
                dir_image = os.path.join(path_image_data, patient.patient_name)
                if not os.path.exists(dir_image):
                    os.makedirs(dir_image)
                # Save the captured image into the datasets folder
                cv2.imwrite("{}/{}.jpg".format(dir_image, count), face)
                cv2.imshow('frame', gray)
                cv2.waitKey(1)
            if count >= 10:
                print("10 face sample and stop dataset")
                break

        capt.release()
        cv2.destroyAllWindows()

    # save data
    data={"encodings": knownEncodings, "names": knownNames}
    try:
        f = open(encoding_file, "wb")
        f.write(pickle.dumps(data))
        f.close()
    except:
        print("[Error] : Can't save the encoding file in {}.\n Please check again.".formate(encoding_file))


def train():
    print("[INFO] : Getting Patients data from Firebase Storage.\n")
    patients=get_patient_infos()

    if patients.__len__() > 0:
        print("[INFO] : Downloading video file from Firebase Storage according to the Patient data.\n")
        patients=download_video(patients)
    else:
        print("[Warning] : None is the Patients data in the Firebase Storage.\n")
        exit(0)

    print("[INFO] : Processing of encoding for the Patient Dataset.\n")
    capture_encode_faces(patients)
    print("[INFO] : End of Processing.")


if __name__ == "__main__":

    # patient = Patient(pname="test", pid="", rname="", allow=False, vname="", vid=path_for_videos+"/1604285939539.mp4")
    # patient.video_local_path = path_for_videos+"/1604285939539.mp4"
    # capture_encode_faces([patient])
    train()
#
