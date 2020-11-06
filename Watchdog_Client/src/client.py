import cv2
import numpy as np
import socket
import argparse
import copy
import imutils
from imutils.video import WebcamVideoStream
from imutils.video import FPS
import firebase_admin
import pyrebase
from firebase_admin import credentials
import base64
import requests
import json
import threading

config = {
    "apiKey": "AIzaSyDwJhRaVMa_RSN8KrKhkFhQ4NUsCTQaCIQ",
    "authDomain": "raspconnect-3850a.firebaseapp.com",
    "databaseURL": "https://raspconnect-3850a.firebaseio.com",
    "projectId": "raspconnect-3850a",
    "storageBucket": "raspconnect-3850a.appspot.com",
    "serviceAccount": "raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json",
    "messagingSenderId": "531382239611",
    "appId": "1:531382239611:web:b3075a4b76fd57eabf3dde",
    "measurementId": "G-7FNNPJ9NJL"
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
cred = credentials.Certificate("raspconnect-3850a-firebase-adminsdk-qf2om-c974c2b381.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://raspconnect-3850a.firebaseio.com",
    "databaseAuthVariableOverride": None
})
db = firebase.database()

from src.detector import Detectors
from src.tracker import Tracker
# from src.counting import *

_lock = threading.Lock()
_server_ip = '192.168.192.50'
_port_number = '5000'
_phone_number = '123456789'

_detector = Detectors()
_tracker = Tracker(dist_thresh=80, max_frames_to_skip=50, max_trace_length=5, axis='x', direction=1)
_diret_id = 0
_roi_line = []
_total_in, _total_ou = 0, 0

_banner_shape = [50, 150]
_spaces = [.1, .4, .8]
_s_point, _e_point = (0, 0), (0, 0)

track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                (0, 255, 255), (255, 0, 255), (255, 127, 255),
                (127, 0, 255), (127, 0, 127)]



def upload_images_firebase(persons):
    for person in persons:
        filename = '../images/{}.jpg'.format(person.person_id)
        cv2.imwrite(filename, person.person_face)
        path_on_cloud = ("photos/{}.jpg".format(person.person_id))
        path_on_local = (filename)
        storage.child(path_on_cloud).put(path_on_local)



def recog_new_person(persons=[]):
    global _server_ip
    global _port_number
    global _phone_number

    if persons.__len__() < 1:
        return
    addr = 'http://{}:{}'.format(_server_ip, _port_number)
    api_url = addr + '/api/receiver'
    print("[INFO] server-url {}\n".format(api_url))

    # prepare headers for http request
    content_type = 'json'
    headers = {'content-type': content_type}

    ids = ''
    txt_images = ''
    for person in persons:
        # Convert captured image to JPG
        retval, img_encoded = cv2.imencode('.jpg', person.person_face)
        if retval:
            # Convert to base64 encoding and show start of data
            ids += '{}@'.format(person.person_id)
            txt_images += '{}@'.format((base64.b64encode(img_encoded)).decode('utf-8'))
    ids = ids[:-1] if ids.__len__() > 0 else ids
    txt_images = txt_images[:-1] if txt_images.__len__() > 0 else txt_images

    data = 'person_ids:{};'.format(ids)
    data += 'person_imgs:{};'.format(txt_images)
    print("[INFO] upload-data : {}".format(data))
    try:
        response = requests.post(api_url, data=data, headers=headers)
        if response.status_code == 400:
            raise Exception(json.loads(response.text)['message'])
        else:
            ids = json.loads(response.text)['person_ids'].split('@')
            names = json.loads(response.text)['person_names'].split('@')
            print(ids)
            print(names)

            if ids.__len__() > 0:
                _lock.acquire()
                try:
                    for i, id in enumerate(ids):
                        delete_persons = []
                        for j, person in enumerate(_tracker.persons):
                            if int(id) == int(person.person_id):
                                if names[i] == 'Unknown':
                                    _tracker.persons[j].cnt_failed += 1
                                    _tracker.persons[j].person_name='Unknown'
                                else:
                                    _tracker.persons[j].person_name = names[i]
                                    same_persons = []
                                    for k, p in enumerate(_tracker.persons):
                                        if k == j:
                                            continue
                                        if p.person_name == names[i]:
                                            same_persons.append(p)
                                    if same_persons.__len__() > 0:
                                        _tracker.persons[j].fpos = same_persons[0].fpos
                                        _tracker.persons[j].processed = _tracker.persons[j].processed | same_persons[0].processed
                                        delete_persons += same_persons
                                break
                        if delete_persons.__len__() > 0:
                            temp = [p for p in _tracker.persons if p not in delete_persons]
                            _tracker.persons = temp
                finally:
                    _lock.release()

    except:
        raise Exception("Can't access to Server.")

def calc_allow_points():
    global _diret_id
    global _s_point, _e_point,  _banner_shape, _spaces

    if _diret_id == 0:
        _s_point=(int(_banner_shape[1] * _spaces[2]),    int(_banner_shape[0] * .5))
        _e_point=(int(_banner_shape[1] * .95),           int(_banner_shape[0] * .5))
    elif _diret_id == 1:
        _e_point=(int(_banner_shape[1] * _spaces[2]),   int(_banner_shape[0] * .5))
        _s_point=(int(_banner_shape[1] * .95),          int(_banner_shape[0] * .5))
    elif _diret_id == 2:
        _s_point=(int(_banner_shape[1] * ((1.0 -_spaces[2]) / 2 + _spaces[2])), int(_banner_shape[0] * .1))
        _e_point=(int(_banner_shape[1] * ((1.0 -_spaces[2]) / 2 + _spaces[2])), int(_banner_shape[0] * .9))
    elif _diret_id == 3:
        _e_point=(int(_banner_shape[1] * ((1.0-_spaces[2]) / 2+_spaces[2])), int(_banner_shape[0] * .1))
        _s_point=(int(_banner_shape[1] * ((1.0-_spaces[2]) / 2+_spaces[2])), int(_banner_shape[0] * .9))
    else:
        raise Exception("Error in allow-line points.")


def drawInfo(frame, persons):
    # draw roi line'
    global _roi_line, _total_in, _total_ou
    global _s_point, _e_point, _banner_shape, _spaces

    cv2.line(frame, _roi_line[0], _roi_line[1], (134, 234, 123), 2)
    banner = np.zeros((_banner_shape[0], _banner_shape[1], 3), dtype='uint8')
    frame[0:_banner_shape[0], 0:_banner_shape[1]] = banner
    cv2.putText(frame, 'IN', (int(_banner_shape[1] * _spaces[0]), int(_banner_shape[0] * .45)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, 'OUT', (int(_banner_shape[1] * _spaces[1]), int(_banner_shape[0] * .45)), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, str(_total_in), (int(_banner_shape[1] * _spaces[0]), int(_banner_shape[0] * .95)), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, str(_total_ou), (int(_banner_shape[1] * _spaces[1]), int(_banner_shape[0] * .95)), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.arrowedLine(frame, _s_point, _e_point, (255, 255, 255), 2)

    for i in range(len(persons)):
        print('-'*100)
        print(persons[i].person_name)
        print(persons[i].cnt_failed)
        print('-' * 100)
        if (len(persons[i].trace) > 1):
            for j in range(len(persons[i].trace) - 1):
                # Draw trace line
                x1 = persons[i].trace[j][0][0]
                y1 = persons[i].trace[j][1][0]
                x2 = persons[i].trace[j + 1][0][0]
                y2 = persons[i].trace[j + 1][1][0]
                clr = persons[i].person_id % 9
                cv2.arrowedLine(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                                track_colors[clr], 2)
                trace_i = len(persons[i].trace) - 1
                trace_x = persons[i].trace[trace_i][0][0]
                trace_y = persons[i].trace[trace_i][1][0]

                if persons[i].person_name == "":
                    cv2.putText(frame, 'ID: ' + str(persons[i].person_id), (int(trace_x), int(trace_y)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (255, 255, 255), 1, cv2.LINE_AA)
                else:
                    cv2.putText(frame, 'Name: ' + str(persons[i].person_name), (int(trace_x), int(trace_y)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (255, 255, 255), 1, cv2.LINE_AA)

def main():
    global _roi_line, _diret_id
    global _total_in, _total_ou
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--num-frames", type=int, default=500,
                        help="# of frames to loop over for FPS test")
    cap = WebcamVideoStream(src=0).start()

    fps = FPS().start()

    # config counting
    frame = cap.read()
    if frame is None:
        raise Exception("Can't open the camera. so it can't config the counting module.")
    (h, w, c) = frame.shape
    _roi_line = _tracker.counting_config(shape=(w, h), percent=50)
    _diret_id = _tracker.get_direct_id()
    calc_allow_points()

    while (True):
        # Capture frame-by-frame
        frame = cap.read()
        if frame is None:
            break
        frame = imutils.resize(frame)

        # Make copy of original frame
        detect_infos = _detector.detect_face(frame)
        if (len(detect_infos) > 0):
            # Track object using Kalman Filter
            new_persons = []
            _lock.acquire()
            try:
                new_persons, del_persons, check_persons = _tracker.Update(detect_infos)
                cnt_in, cnt_ou = _tracker.counting()
            finally:
                _lock.release()
            if check_persons.__len__() > 0:
                th = threading.Thread(target=recog_new_person, args=(_tracker.persons,))
                th.start()
            # if check_persons.__len__() > 0:
            #     th = threading.Thread(target=recog_new_person, args=(check_persons,))
            #     th.start()
            # if new_persons.__len__() > 0:
            #     th1 = threading.Thread(target=upload_images_firebase, args=(new_persons, ))
            #     th1.start()
            _total_in += cnt_in
            _total_ou += cnt_ou
            # For identified object tracks draw tracking line
            # Use various colors to indicate different track_id

        drawInfo(frame, _tracker.persons)

        cv2.imshow('Tracking', frame)

        # Check for key strokes
        fps.update()
        k = cv2.waitKey(50) & 0xff
        if k == 27:  # 'esc' key has been pressed, exit program.
            break
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    cap.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
    # execute main
    # persons = []
    # p = Person([], cv2.imread('../images/image1.jpeg'), 1)
    # persons.append(p)
    # p = Person([], cv2.imread('../images/image2.jpeg'), 2)
    # persons.append(p)
    # upload_information(persons)
    # main()