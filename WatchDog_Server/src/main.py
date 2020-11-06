import cv2
import os
import firebase_admin
import pyrebase
from firebase_admin import credentials
from src import watcher, encode_faces
from src.watcher import Watcher

config={
    "apiKey": "AIzaSyDwJhRaVMa_RSN8KrKhkFhQ4NUsCTQaCIQ",
    "authDomain": "raspconnect-3850a.firebaseapp.com",
    "databaseURL": "https://raspconnect-3850a.firebaseio.com",
    "projectId": "raspconnect-3850a",
    "storageBucket": "raspconnect-3850a.appspot.com",
    "serviceAccount": "/home/chirag/Documents/Code_new/WatchDog_Server/src/raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json",
    "messagingSenderId": "531382239611",
    "appId": "1:531382239611:web:b3075a4b76fd57eabf3dde",
    "measurementId": "G-7FNNPJ9NJL"
}

firebase=pyrebase.initialize_app(config)
storage=firebase.storage()
cred=credentials.Certificate(
    "/home/chirag/Documents/Code_new/WatchDog_Server/src/raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://raspconnect-3850a.firebaseio.com",
    "databaseAuthVariableOverride": None
})
db=firebase.database()


def stream_handler(message):
    ab=str(1)
    ba=str(1)

    files=storage.child('/').list_files()
    vidfiles=storage.child('/').list_files()

   # path_for_images="/home/chirag/PycharmProjects/WatchDog_Server/images_to_recognise"
    path_for_videos="/home/chirag/Documents/Code_new/WatchDog_Server/media"

    node=str(message["path"]).split('/')[-2]  # you can slice the path according to your requirement
    property=str(message["path"]).split('/')[-1]
    value=message["data"]
    if (message["event"] == "put"):
        for vid in vidfiles:
            try:
                if "videos/" in vid.name:
                    if vid.name == "videos/":
                        continue
                    else:
                        storage.child(vid.name).download(path_for_videos+"/"+ba+".mp4")
                        y=int(ba)
                        ba=str(y+1)
            except:
                print("video fail to download")
    else:
        print("error")

my_stream=db.child('/').stream(stream_handler)

watch_file='/home/chirag/Documents/Code_new/WatchDog_Server/media'

def capture_encode_faces():
    path="/home/chirag/Documents/Code_new/WatchDog_Server/media/"
    capt=cv2.VideoCapture(path+'1.mp4')
    dir="/home/chirag/Documents/Code_new/WatchDog_Server/dataset"
    face_id='Valay'
    count=0
    while (capt.isOpened()):
        face_detector=cv2.CascadeClassifier(
            '/home/chirag/Documents/Code_new/WatchDog_Server/cascades/haarcascade_frontalface_alt2.xml')
        ret, frame=capt.read()
        if ret == True:
            gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces=face_detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(gray, (x, y), (x+w, y+h), (255, 0, 0), 2)
                count+=1
                dir1=os.path.join(dir, face_id)
                if not os.path.exists(dir1):
                    os.makedirs(dir1)
                # Save the captured image into the datasets folder
                cv2.imwrite(dir1+"/"+str(count)+".jpg",
                            gray[y:y+h, x:x+w])
                cv2.imshow('frame', gray)
            if count >= 10:
                print("10 face sample and stop dataset")
                break
        else:
            break
    capt.release()
    cv2.destroyAllWindows()
    encode_faces.encoding()
    print("encoded images")

def custom_action():
    capture_encode_faces()

watch1=Watcher(watch_file, custom_action)  # also call custom action function
watch1.watch()# start the watch going
watch1.look()















