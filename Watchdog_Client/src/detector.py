import numpy as np
import cv2
import datetime

class Detectors(object):
    face_cascade = cv2.CascadeClassifier('../cascades/haarcascade_frontalface_alt2.xml')
    firstFrame = None

    def __init__(self):
        self.fgbg = cv2.createBackgroundSubtractorMOG2()
        self.count = 0
        
    def detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        face_infos = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3,
                                                 minNeighbors=5)

        detect_info = []
        for (x, y, w, h) in face_infos:
            b = np.array([[x+w / 2], [y+h / 2]])
            face_img = frame[y:y + h, x:x + w]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            detect_info.append([np.round(b), face_img])     # center point, face image
        return detect_info
