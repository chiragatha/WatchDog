import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import cv2
from datetime import datetime
import base64
import json

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
tokens = ["f74Jkk84SxyL7lvSwUsPGY:APA91bFTYXtMn9ffwM8rtba2TmlfEVD_592WdLAy_mw8hClANjQ27jENkZ4brBzRNtnSxASyRr8ZgK0zr4RLMBRZ26OTvHOnpC0L_EGYZWAcvhFXmyfOYwekj9vrdp-_sCDTLW9bZ22f"]
myjsonfile = open('./jetson/jetson_config.json','r')
jsondata = myjsonfile.read()

def sendPushNotification(image=None, size=(64, 64), name='', inout=0, phone_token=tokens, title='Emergency !'):
    # check parameters
    if image is None:
        raise Exception("Error of Image Data.")
    try:
        image=cv2.resize(image, size)
    except:
        raise Exception("Can't resize the person image into LargeIcon Data.")
    if name == '':
        raise Exception("Error of Person Name.")
    if phone_token.__len__() < 1:
        raise Exception("Error of Token Infos.")
    now=datetime.now()
    dtime=now.strftime("%H:%M:%S")
    msg_content = "Error!"
    if inout == 0:
        msg_content = "{} has arrived in the room at {}.".format(name, dtime)
    elif inout == 1:
        msg_content="{} has left from the room at {}.".format(name, dtime)

    retval, img_encoded=cv2.imencode('.jpg', image)

    if not retval:
        raise Exception("Can't convert the image into the text data.")
        # Convert to base64 encoding and show start of data
    txt_image=base64.b64encode(img_encoded).decode('utf-8')

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=msg_content
            ),
            data={"image": str(txt_image)},
            tokens=phone_token,
        )

        # Send a message to the device corresponding to the provided
        # registration token.
        response = messaging.send_multicast(message)
        print(response.__str__())
        # Response is a message ID string.
        print('Successfully sent message:', response)
    except:
        raise Exception("Failed to send the notification.")



def sendPush(title, msg, registration_token, dataObject=None):
    # See documentation on defining a message payload.
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=dataObject,
        tokens=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send_multicast(message)
    print(response.__str__())
    # Response is a message ID string.
    print('Successfully sent message:', response)

image = cv2.imread('../../src/test.jpg')
sendPushNotification(image=image, name="Person")