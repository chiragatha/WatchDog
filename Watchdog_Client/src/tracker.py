# Import python libraries
import numpy as np
import uuid
from scipy.optimize import linear_sum_assignment

# from src.common import dprint
from src.kalman_filter import KalmanFilter
import threading
from src.sms_phone import *

class Person(object):
    """Track class for every object to be tracked
    Attributes:
        None
    """

    def __init__(self, prediction, face, trackIdCount):
        """Initialize variables used by Track class
        Args:
            prediction: predicted centroids of object to be tracked
            trackIdCount: identification of each track object
        Return:
            None
        """
        self.person_id = trackIdCount    # identification of each track object
        self.person_name = ""
        self.person_face = face
        self.KF = KalmanFilter()        # KF instance to track this object
        self.prediction = np.asarray(prediction)  # predicted centroids (x,y)
        self.skipped_frames = 1         # number of frames skipped undetected
        self.trace = []                 # trace path
        self.fpos = [prediction[0], prediction[1]]
        self.processed = False
        self.cnt_failed = 0


class Tracker(object):
    """Tracker class that updates track vectors of object tracked
    Attributes:
        None
    """

    def __init__(self, dist_thresh, max_frames_to_skip, max_trace_length, axis='x', direction=0, max_fails=10):
        """Initialize variable used by Tracker class
        Args:
            dist_thresh: distance threshold. When exceeds the threshold,
                         track will be deleted and new track is created
            max_frames_to_skip: maximum allowed frames to be skipped for
                                the track object undetected
            max_trace_lenght: trace path history length
            trackIdCount: identification of each track object
        Return:
            None
        """
        self.dist_thresh = dist_thresh
        self.max_frames_to_skip = max_frames_to_skip
        self.max_trace_length = max_trace_length
        self.persons = []
        self.axis = axis
        self.direction = direction
        self.line_x = -1
        self.line_y = -1
        self.max_fails = max_fails

    def counting_config(self, shape, percent):

        sp, ep = (0, 0), (0, 0)

        percent = max(0, min(100, percent))
        if self.axis == 'x':
            self.line_x = int(shape[0] * percent / 100)
            sp = (self.line_x, 0)
            ep = (self.line_x, shape[1])

        if self.axis == 'y':
            self.line_y = int(shape[1] * percent / 100)
            sp = (0, self.line_y)
            ep = (shape[0], self.line_y)
        return [sp, ep]

    def get_direct_id(self):
        id = 0  # 0 :left->right, 1 : right->left, 2 : top->bottom, 3: bottom->top // in->out
        if self.axis == 'x':
            id = self.direction
        if self.axis == 'y':
            id = 2 + self.direction
        return id

    def Update(self, detect_infos):
        """Update tracks vector using following steps:
            - Create tracks if no tracks vector found
            - Calculate cost using sum of square distance
              between predicted vs detected centroids
            - Using Hungarian Algorithm assign the correct
              detected measurements to predicted tracks
              https://en.wikipedia.org/wiki/Hungarian_algorithm
            - Identify tracks with no assignment, if any
            - If tracks are not detected for long time, remove them
            - Now look for un_assigned detects
            - Start new tracks
            - Update KalmanFilter state, lastResults and tracks trace
        Args:
            detections: detected centroids of object to be tracked
        Return:
            None
        """


        # Calculate cost using sum of square distance between
        # predicted vs detected centroids
        N = len(self.persons)
        M = len(detect_infos)
        cost = np.zeros(shape=(N, M))   # Cost matrix
        for i in range(len(self.persons)):
            for j in range(len(detect_infos)):
                try:
                    diff = self.persons[i].prediction - detect_infos[j][0]
                    distance = np.sqrt(diff[0][0]*diff[0][0] +
                                       diff[1][0]*diff[1][0])
                    cost[i][j] = distance
                except:
                    pass

        # Let's average the squared ERROR
        cost = (0.5) * cost
        # Using Hungarian Algorithm assign the correct detected measurements
        # to predicted tracks
        assignment = []
        for _ in range(N):
            assignment.append(-1)
        row_ind, col_ind = linear_sum_assignment(cost)
        for i in range(len(row_ind)):
            assignment[row_ind[i]] = col_ind[i]

        # Identify tracks with no assignment, if any
        un_assigned_persons = []
        for i in range(len(assignment)):
            if (assignment[i] != -1):
                # check for cost distance threshold.
                # If cost is very high then un_assign (delete) the track
                if (cost[i][assignment[i]] > self.dist_thresh):
                    assignment[i] = -1
                    un_assigned_persons.append(i)
                pass
            else:
                self.persons[i].skipped_frames += 1
                self.persons[i].cnt_failed = 0

        # If tracks are not detected for long time, remove them
        del_person_ids = []
        del_persons = []
        for i in range(len(self.persons)):
            if (self.persons[i].skipped_frames > self.max_frames_to_skip):
                del_person_ids.append(i)
        if len(del_person_ids) > 0:  # only when skipped frame exceeds max
            for id in del_person_ids:
                if id < len(self.persons):
                    del_persons.append(self.persons[id])
                    del self.persons[id]
                    del assignment[id]
                else:
                    print("ERROR: id is greater than length of tracks")

        # Now look for un_assigned detects
        un_assigned_detects = []
        for i in range(len(detect_infos)):
                if i not in assignment:
                    un_assigned_detects.append(i)

        # Start new persons
        check_persons = []
        if(len(un_assigned_detects) != 0):
            for i in range(len(un_assigned_detects)):
                person = Person(detect_infos[un_assigned_detects[i]][0], detect_infos[un_assigned_detects[i]][1],
                                int(str(uuid.uuid1().int)[-4:]))
                self.persons.append(person)
                check_persons.append(person)

        # Update KalmanFilter state, lastResults and tracks trace
        for i in range(len(assignment)):
            self.persons[i].KF.predict()

            if(assignment[i] != -1):
                self.persons[i].skipped_frames = 10
                self.persons[i].prediction = self.persons[i].KF.correct(
                                            detect_infos[assignment[i]][0], 1)
            else:
                self.persons[i].prediction = self.persons[i].KF.correct(
                                            np.array([[0], [0]]), 0)

            if(len(self.persons[i].trace) > self.max_trace_length):
                for j in range(len(self.persons[i].trace) -
                               self.max_trace_length):
                    del self.persons[i].trace[j]

            self.persons[i].trace.append(self.persons[i].prediction)
            self.persons[i].KF.lastResult = self.persons[i].prediction

        new_persons = []
        for person in self.persons:
            if person not in check_persons:
                if person.person_name == "Unknown" and person.cnt_failed > self.max_fails:
                    new_persons.append(person)
        return new_persons, del_persons, check_persons

    def counting(self):
        in_p, ou_p = 0, 0
        in_people, ou_people = [], []

        for i, person in enumerate(self.persons):
            if person.processed:
                continue
            if person.trace.__len__() < 1:
                continue
            if self.axis == 'x':
                if self.direction == 0:  # left-right : in->out
                    if person.fpos[0] < self.line_x and person.trace[-1][0][0] > self.line_x:
                        self.persons[i].processed = True
                        ou_p += 1
                        ou_people.append(self.persons[i])
                    if person.fpos[0] > self.line_x and person.trace[-1][0][0] < self.line_x:
                        self.persons[i].processed = True
                        in_p += 1
                        in_people.append(self.persons[i])
                if self.direction == 1:  # right-left : in->out
                    if person.fpos[0] > self.line_x and person.trace[-1][0][0] < self.line_x:
                        self.persons[i].processed = True
                        ou_p += 1
                        ou_people.append(self.persons[i])
                    if person.fpos[0] < self.line_x and person.trace[-1][0][0] > self.line_x:
                        self.persons[i].processed = True
                        in_p += 1
                        in_people.append(self.persons[i])

            if self.axis == 'y':
                if self.direction == 0:  # top-bottom : in->out
                    if person.fpos[1] < self.line_y and person.trace[-1][1][0] > self.line_y:
                        self.persons[i].processed = True
                        ou_p += 1
                        ou_people.append(self.persons[i])
                    if person.fpos[1] > self.line_y and person.trace[-1][1][0] < self.line_y:
                        self.persons[i].processed = True
                        in_p += 1
                        in_people.append(self.persons[i])
                if self.direction == 1:  # bottom-top : in->out
                    if person.fpos[1] > self.line_y and person.trace[-1][1][0] < self.line_y:
                        self.persons[i].processed = True
                        ou_p += 1
                        ou_people.append(self.persons[i])
                    if person.fpos[1] < self.line_y and person.trace[-1][1][0] > self.line_y:
                        self.persons[i].processed = True
                        in_p += 1
                        in_people.append(self.persons[i])
        if in_people.__len__() > 0:
            th2 = threading.Thread(target=sendMultiPush, args=(in_people, ))
            th2.start()
        if ou_people.__len__() > 0:
            th3 = threading.Thread(target=sendMultiPush, args=(ou_people, ))
            th3.start()

        return in_p, ou_p