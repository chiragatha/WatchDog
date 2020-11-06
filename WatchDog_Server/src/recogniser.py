# import the necessary packages
import face_recognition
import pickle
import cv2
import time
# construct the argument parser and parse the arguments


_detection_method = "hog"
_encodings_path = "encodings.pickle"

# load the known faces and embeddings



def recog(image, _updateing):
    if _updateing:
        return "Unknown"
    print("[INFO] loading encodings...")
    try:
        data=pickle.loads(open(_encodings_path, "rb").read())
    except:
        raise Exception("Can't open the Pickle File.")
    stime = time.time()
    # load the input image and convert it from BGR to RGB
    print("[INFO] recognizing faces...")
    boxes = face_recognition.face_locations(image, model=_detection_method)
    encodings = face_recognition.face_encodings(image, boxes)
    # initialize the list of names for each face detected
    names = []
    # loop over the facial embeddings
    for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"
        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchedIdxs=[i for (i, b) in enumerate(matches) if b]
            counts={}
            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                name=data["names"][i]
                counts[name]=counts.get(name, 0)+1
            # determine the recognized face with the largest number of
            # votes (note: in the event of an unlikely tie Python will
            # select first entry in the dictionary)
            name=max(counts, key=counts.get)

        # update the list of names
        names.append(name)

    print("[Time] {:.03}".format(time.time()-stime))
    print(names)
    print("[INFO] done recognition...")
    if names.__len__() > 0:
        return names[0]
    return "Unknown"
    