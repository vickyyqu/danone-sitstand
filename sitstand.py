import cv2
import mediapipe as mp
import streamlit as st
import numpy as np
import time

st.set_page_config(layout="wide")

# Initialize Mediapipe Pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def process_image(image):
    ## Crop image to 1x1 square
    height, width, _ = image.shape

    size = min(height, width)
    start_x = (width - size) // 2
    start_y = (height - size) // 2

    cropped_image = image[start_y:start_y + size, start_x:start_x + size]

    ## CLAHE (Adaptive Histogram Equalization)
    lab = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
    l_clahe = clahe.apply(l)

    lab = cv2.merge((l_clahe, a, b))
    image_clahe = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    return image_clahe


# Function to calculate angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)  # First point
    b = np.array(b)  # Midpoint
    c = np.array(c)  # Last point
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Function to process the video frame and count squats
def squat_counter(timer_duration, label_placeholder, countdown_placeholder, cap, pose, time_placeholder, correct_placeholder, incorrect_placeholder):
    counter = 0
    incorrect_counter = 0
    stage = "State 1"
    prev_knee_angle = 0

    # Start 5s countdown to test
    label_placeholder.warning(f"Get ready! The timer will run for 30 seconds.")
    with countdown_placeholder:
        for seconds in range(5):
            st.subheader(f"⏳ Starting in {5-seconds}s...")
            time.sleep(1)
    countdown_placeholder.empty()

    # Test start
    label_placeholder.info("Start sitting and standing on the chair!")
    start_time = time.time()
    elapsed_time = time.time() - start_time

    stage_1 = False
    stage_2 = False
    stage_3 = False
    stage_4 = False


    while elapsed_time <= timer_duration:
        ret, frame = cap.read()
        if not ret:
            st.error("Camera feed lost.")
            break
        
        uncropped_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = process_image(uncropped_image)
        image = np.ascontiguousarray(image) 
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            landmarks = results.pose_landmarks.landmark
            left_visibility = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility
            right_visibility = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].visibility

            if left_visibility > right_visibility:
                hip = [landmarks[23].x, landmarks[23].y]
                knee = [landmarks[25].x, landmarks[25].y]
                ankle = [landmarks[27].x, landmarks[27].y]
                toe = [landmarks[31].x, landmarks[31].y]
                shoulder = [landmarks[11].x, landmarks[11].y]
            else:
                hip = [landmarks[24].x, landmarks[24].y]
                knee = [landmarks[26].x, landmarks[26].y]
                ankle = [landmarks[28].x, landmarks[28].y]
                toe = [landmarks[32].x, landmarks[32].y]
                shoulder = [landmarks[12].x, landmarks[12].y]

            normal = [hip[0], hip[1] - 0.5]
            knee_angle = calculate_angle(hip, knee, ankle)
            back_angle = calculate_angle(shoulder, hip, normal)
        

            ## STATE 1: upright position
            if knee_angle >= 160 and 0 <= back_angle <= 20 :
                stage_1 = True
                stage = "State 1"

            ## STATE 4: sitting -> half-sit
            elif stage == "State 3" and knee_angle > 120 and knee_angle < 155:
                stage = "State 4"
                stage_1 = False
                stage_4 = True
            
            ## STATE 2: half-sit -> sitting
            elif stage != "State 3" and knee_angle > 120 and knee_angle < 160:
                stage_2 = True
                stage = "State 2"

            ## STATE 3: half-sit -> sitting 
            elif stage == "State 2" and knee_angle <= 120: ## and knee angle reached a local minima
                if 0 <= back_angle <= 20 : ## back is straight
                    stage_3 = True

                    # increment correct counter
                    # if not stage_1:
                    #     incorrect_counter += 1
                        # stage_3 = False
                        # st.write("never straight back")

                else: 
                    incorrect_counter += 1
                    # stage_3 = False
                    # st.write("lean too far back")

                stage = "State 3"
            

            # increment correct counter
            if stage_1 and stage_2 and stage_3 and stage_4:
                counter += 1

                stage_1 = False
                stage_2 = False
                stage_3 = False
                stage_4 = False
            
            prev_knee_angle = knee_angle

        except:
            pass
        
        # Include only body landmarks
        body_landmarks = results.pose_landmarks

        try:
            for i in range(11):  # Exclude indices 0 to 10 (facial landmarks)
                body_landmarks.landmark[i].visibility = 0
        except:
            pass

        mp_drawing.draw_landmarks(image, body_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

        elapsed_time = time.time() - start_time
        time_placeholder.metric(f"⏳ Remaining time (s): ", value=round(abs(timer_duration - elapsed_time), 1))

        # Display window with landmarks
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        stframe.image(image, channels="RGB", use_container_width=True)

        # Update counters live
        correct_placeholder.metric(label="Correct Sit-Stands", value=counter, border=True)
        incorrect_placeholder.metric(label="Incorrect Sit-Stands", value=incorrect_counter, border=True)
    
    # Time is up
    label_placeholder.error("Time is up!")
    return counter, incorrect_counter



##################### UI ELEMENTS #####################
side1, title, app, side2 = st.columns([1,6,6,1])

with title:
    st.logo('/Users/vickyqu/Desktop/sitstand/elements/4cbf74941a44a7901a19bc01a37fd6e6f094a70c3a767afc7af1cfa994d6f485.png', size="large")
    st.header("AI-Based Sit-Stand Test!", divider=True)

    timer_duration = 30

    label_placeholder = st.empty()
    label_placeholder.info("🪑 How many sit and stands can you do within 30 seconds? Try it now!")
    countdown_placeholder = st.empty()
    time_placeholder = st.empty()
    stage_a = st.empty()
    knee_a = st.empty()
    back_a = st.empty()
    up_a = st.empty()


with app:
    # Initalise pose model
    with mp_pose.Pose(min_detection_confidence=0.4, min_tracking_confidence=0.4) as pose:
        cap = cv2.VideoCapture(0)
        stframe = st.empty()
        button_placeholder = st.empty()
        start_button = button_placeholder.button("Start Sit-Stand Counter", use_container_width=True, type="primary")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("Unable to access the camera.")
                break
            
            uncropped_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = process_image(uncropped_image)
            image = np.ascontiguousarray(image) 
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark
                left_visibility = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility
                right_visibility = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].visibility

                if left_visibility > right_visibility:
                    hip = [landmarks[23].x, landmarks[23].y]
                    knee = [landmarks[25].x, landmarks[25].y]
                    ankle = [landmarks[27].x, landmarks[27].y]
                    toe = [landmarks[31].x, landmarks[31].y]
                    shoulder = [landmarks[11].x, landmarks[11].y]
                else:
                    hip = [landmarks[24].x, landmarks[24].y]
                    knee = [landmarks[26].x, landmarks[26].y]
                    ankle = [landmarks[28].x, landmarks[28].y]
                    toe = [landmarks[32].x, landmarks[32].y]
                    shoulder = [landmarks[12].x, landmarks[12].y]

            except:
                pass
            
            # Include only body landmarks
            body_landmarks = results.pose_landmarks

            try:
                for i in range(11):  # Exclude indices 0 to 10 (facial landmarks)
                    body_landmarks.landmark[i].visibility = 0
            except:
                pass

            mp_drawing.draw_landmarks(image, body_landmarks, mp_pose.POSE_CONNECTIONS,
                                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
            
            # Display camera if not running
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            stframe.image(image, channels="RGB", use_container_width=True)


            # Start sit stand tracking
            if start_button:
                st.session_state.function_executed = True

                with title:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        correct_placeholder = st.empty()
                    with col2:
                        incorrect_placeholder = st.empty()

                    finish_message = st.empty()

                counter, incorrect_counter = squat_counter(timer_duration, label_placeholder, countdown_placeholder, cap, pose, time_placeholder, correct_placeholder, incorrect_placeholder)


                # Display success message
                if counter >= 10:
                    finish_message.success(f"🎉 Wow great job! You did {counter} sit and stands in 30 seconds, keep it up!")
                    st.balloons()
                    st.balloons()
                else:
                    finish_message.warning(f" 🙌 Good effort, only {10-counter} more to go! Try again?")

                start_button = None


        cap.release()