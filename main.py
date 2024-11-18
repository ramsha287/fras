from fastapi import FastAPI, File, UploadFile, Form
import cv2
import face_recognition
import numpy as np
import os
import csv
from datetime import datetime
from pydantic import BaseModel
import threading


app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)



STUDENT_IMAGES_DIR = "faces"
ATTENDANCE_FILE = "attendance.csv"

known_face_encodings = []
known_face_names = []

attendance_running = False

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


load_known_faces()


@app.post("/enroll/")
async def enroll_student(name: str = Form(...), file: UploadFile = File(...)):
    try:
        
        file_location = f"{STUDENT_IMAGES_DIR}/{name}.jpeg"  
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        
        student_name = name

        image = face_recognition.load_image_file(file_location)
        encoding = face_recognition.face_encodings(image)[0]

        known_face_encodings.append(encoding)
        known_face_names.append(student_name)

        return {"message": f"Student {student_name} enrolled successfully!"}

    except Exception as e:
        return {"error": str(e)}

def mark_attendance():
    global attendance_running
   
    video_capture = cv2.VideoCapture(0)
    attendance_logged = set()  # Set to track logged faces

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    with open(ATTENDANCE_FILE, "a", newline="") as f:
        lnwriter = csv.writer(f)

        while attendance_running:
            _, frame = video_capture.read()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distance = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distance)

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    if name not in attendance_logged:
                        current_time = now.strftime("%H:%M:%S")
                        lnwriter.writerow([name, current_time])  # Write to CSV
                        attendance_logged.add(name)  # Add to logged faces
                        print(f"Attendance marked for {name} at {current_time}")

                    cv2.putText(frame, f"{name} Present", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            cv2.imshow("Attendance", frame)

            
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
