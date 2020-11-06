from flask import Flask, request, Response
import os
import jsonpickle
import numpy as np
import cv2
import base64
import io
from PIL import Image
import uuid
from src.recogniser import *
from src.train import train

# global variables
_server_ip = "192.168.192.50"
_server_port = 5000
_php_server_port = 8012

_updateing = False
# Initialize the Flask application
app = Flask(__name__)


# route http posts to this method
@app.route('/api/receiver', methods=['POST'])
def receiver():
    r = request
    data = dict(toks.split(":") for toks in (r.data).decode("ascii").split(";") if toks)

    if len(data) != 2:
        response = {'message': 'Incorrect'}
        # encode response using jsonpickle
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=400, mimetype="application/json")
    else:
        ids = data['person_ids'].split('@')
        txt_images = data['person_imgs'].split('@')
        if ids.__len__() != txt_images.__len__():
            response = {'message': 'Data Error'}
            response_pickled = jsonpickle.encode(response)
            return Response(response=response_pickled, status=400, mimetype="application/json")

        names = ''
        for i, img in enumerate(txt_images):
            jpg_as_text = str.encode(img)
            jpg_face = base64.b64decode(jpg_as_text)
            image = Image.open(io.BytesIO(jpg_face))
            face_img = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
            name = recog(face_img, _updateing)
            print(name)
            names += name + "@"
        if len(names) > 0:
            names = names[:-1]
        response = {'person_ids': data['person_ids'], 'person_names': names}
        print(response)
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route('/retrain', methods=['GET', 'POST'])
def retrain():
    _updateing = True
    train()
    _updateing = False
    return "success"


if __name__ == "__main__":
    # start flask app
    app.run(host=_server_ip, port=_server_port)
