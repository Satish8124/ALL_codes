

import cv2
import numpy as np
import mediapipe as mp
from datetime import timedelta, datetime
from scenedetect import detect, ContentDetector # pip install or install from any package manager or from packages within Pycharm would do



mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


# Getting the scene_list for the video

scene_list = detect('C:/Users/INTEL 89/Desktop/MAJOR_CODES_2023/Exercise-CounterCumTimer-main/test/video4.mp4', ContentDetector( threshold = 20))
# printing the scene_list in
for i, scene in enumerate(scene_list):
    print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))



# Capturing the video
cap = cv2.VideoCapture('C:/Users/INTEL 89/Desktop/MAJOR_CODES_2023/Exercise-CounterCumTimer-main/test/video4.mp4')


# Getting the total frames
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Getting FPS from the video
fps = int(cap.get(cv2.CAP_PROP_FPS))


# taking a list of to-be-deleted frames and adding the fps to make it one second
delete = []

# Storing the frames to be deleted
for i, scene in enumerate(scene_list) :
    delete.extend(range(scene[0].get_frames(),scene[0].get_frames() + fps))


# rep Counter
counter = 0
# stage of knee
stage = None
# time elapsed
diff = 0
# start time of the timer
start_time = None



def calculate_angle(h, k, a):  # h=hip, k=knee, a=ankle
    h = np.array(h)  # hip
    k = np.array(k)  # knee
    a = np.array(a)  # ankle

    radians = np.arctan2(h[1] - k[1], a[0] - k[0]) - np.arctan2(h[1] - k[1], h[0] - k[0])
    angle = np.abs(radians * 180.0 / np.pi)

    return angle


## Setup Mediapipe Instances
with mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.5, model_complexity= 1 ) as pose:
    fcount = 0

    while cap.isOpened():

        fcount += 1
        ret, frame = cap.read()
        frame = cv2.resize(frame,(600,600))

        if fcount not in delete:

        # Recolor Image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make Detection
            results = pose.process(image)

            # Recolor back to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Extract Landmarks
            try:
                landmarks = results.pose_landmarks.landmark

                # Get Co-ordinates

                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                # Calculate Angle
                angle = calculate_angle(hip, knee, ankle)

                # visualize
                cv2.putText(image, str(angle),
                            tuple(np.multiply(knee, [854, 640]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            except:
                pass

        # Render details to the window

            # Status Box
            cv2.rectangle(image, (0, 0), (280, 80), (245, 117, 16), -1)

            # Rep heading and counter
            cv2.putText(image, 'REPS', (15, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter), (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            #Knee Bent status
            cv2.putText(image, 'Knee Status', (125, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, stage, (65, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Timer Box
            cv2.rectangle(image, (600, 0), (854, 80), (245, 117, 16), -1)
            # Timer heading
            cv2.putText(image, 'Timer', (700, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 0, 0), 1, cv2.LINE_AA)


            # Render Detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2), )

            # Rep Count Logic

            if angle > 140:                                         # when the angle is greater than 140 degrees
                stage = 'straight knee'


            if angle < 140 and stage == 'straight knee':            # when the angle less than 140 degrees

                start_time = datetime.now()                         # start timer, take current time

                stage = 'bent knee'                                 #set stage to bent


            if start_time and stage == 'bent knee':                 # if the time is non-null (true, or has some value to it) and stage is 'bent knee', this means
                                                                    # that the leg is being bent ( change in state )

                diff = (datetime.now() - start_time).seconds        # take the time elapsed (difference)

                if diff <= 8:                                       # Constantly check if its less than 8 seconds

                    cv2.putText(image, str(diff), (710, 75),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255,  255, 255), 2, cv2.LINE_AA)      # if diff < 8, print the timer to the window


                 # if the timer > 8 and the angle was smaller than 140 degrees, that means a succesfull rep is done
                elif diff > 8 and angle < 140:
                    counter = counter + 1
                    start_time = 0

            if angle > 140 and diff < 8:
                cv2.putText(image, 'keep your knee bent', (150, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)        # if the timer is less than 8 seconds and the angle becomes greater than 140, print feed back to the window

            cv2.imshow('Mediapipe Feed', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()