
# this is data structure of a Patient.
class Patient:
    def __init__(self, pname="", pid="", rname="", allow=False, vname="", vid=""):
        self.patient_name = pname
        self.patient_id = pid
        self.room_name = rname
        self.is_allow = allow
        self.video_name = vname
        self.video_id = vid
        self.video_local_path = None # it shows the video path downlaoded in the local storage from firebase.
