from fastapi import FastAPI, File, UploadFile, Form
import cv2
import face_recognition
import numpy as np
import os
import csv
from datetime import datetime
from pydantic import BaseModel
import threading

# Initialize FastAPI
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains, modify it if you want more control
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Directory to store student images and encodings
STUDENT_IMAGES_DIR = "faces"
ATTENDANCE_FILE = "attendance.csv"

# Initialize known students' encodings and names
known_face_encodings = []
known_face_names = []

# Variable to control webcam
attendance_running = False

# Function to load encodings from saved images
def load_known_faces():
    global known_face_encodings, known_face_names

    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(STUDENT_IMAGES_DIR):
        if filename.endswith(".jpeg"):
            image = face_recognition.load_image_file(f"{STUDENT_IMAGES_DIR}/{filename}")
            encoding = face_recognition.face_encodings(image)[0]
            name = filename.split('.')[0]  # Name from the file name (without extension)
            known_face_encodings.append(encoding)
            known_face_names.append(name)

# Load known faces on startup
load_known_faces()

# Enroll student by uploading an image file and providing a name
@app.post("/enroll/")
async def enroll_student(name: str = Form(...), file: UploadFile = File(...)):
    try:
        # Save the uploaded image
        file_location = f"{STUDENT_IMAGES_DIR}/{name}.jpeg"  # Use the student's name for the filename
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        # Get the student's name (from input) and image encoding
        student_name = name

        # Add encoding for the new student
        image = face_recognition.load_image_file(file_location)
        encoding = face_recognition.face_encodings(image)[0]

        # Update the known faces list
        known_face_encodings.append(encoding)
        known_face_names.append(student_name)

        # Return success response
        return {"message": f"Student {student_name} enrolled successfully!"}

    except Exception as e:
        return {"error": str(e)}

# Function to mark attendance
def mark_attendance():
    global attendance_running
    # Start webcam capture
    video_capture = cv2.VideoCapture(0)
    attendance_logged = set()  # Set to track logged faces

    # Get current date
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    # Open attendance file
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        lnwriter = csv.writer(f)

        while attendance_running:
            _, frame = video_capture.read()

            # Resize frame and convert to RGB for face_recognition
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Recognize faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distance = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distance)

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    # Mark attendance only if not already logged
                    if name not in attendance_logged:
                        current_time = now.strftime("%H:%M:%S")
                        lnwriter.writerow([name, current_time])  # Write to CSV
                        attendance_logged.add(name)  # Add to logged faces
                        print(f"Attendance marked for {name} at {current_time}")

                    # Display the recognized name on the frame
                    cv2.putText(frame, f"{name} Present", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Display the frame with name
            cv2.imshow("Attendance", frame)

            # Break on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        video_capture.release()
        cv2.destroyAllWindows()


        
@app.get("/start-attendance/")
async def start_attendance():
    global attendance_running
    try:
        if not attendance_running:
            attendance_running = True
            thread = threading.Thread(target=mark_attendance)
            thread.start()
            return {"message": "Attendance started", "status": "success"}
        else:
            return {"message": "Attendance is already running", "status": "error"}
    except Exception as e:
        return {"message": f"Error starting attendance: {str(e)}", "status": "error"}


@app.get("/stop-attendance/")
async def stop_attendance():
    global attendance_running
    try:
        if attendance_running:
            attendance_running = False
            return {"message": "Attendance stopped", "status": "success"}
        else:
            return {"message": "Attendance is not running", "status": "error"}
    except Exception as e:
        return {"message": f"Error stopping attendance: {str(e)}", "status": "error"}
