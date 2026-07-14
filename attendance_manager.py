# attendance_manager.py
import cv2
import numpy as np
import logging
import time
from datetime import datetime
from config import Config
from face_recognition_service import load_encodings, recognize_faces
from database import log_attendance

logger = logging.getLogger(__name__)

class AttendanceManager:
    """Manages video capture and face recognition for attendance."""
    
    def __init__(self, branch):
        """Initialize with branch ID to load correct encodings."""
        self.branch = branch
        self.known_face_encodings, self.known_face_names = load_encodings(branch)
        self.last_log_time = {}  # Track last time each person was logged
        self.log_cooldown = 60  # Seconds between attendance logs for same person
        logger.info(f"Initialized AttendanceManager for branch {branch} with {len(self.known_face_encodings)} known faces.")
    
    def generate_frames(self):
        """Generator that yields video frames with face recognition."""
        camera = None
        try:
            # Try to open the camera
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise RuntimeError("Could not start camera.")
            
            # Set camera properties for better performance
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 15)
            
            # Counter for processing only every few frames
            frame_count = 0
            process_interval = 3  # Process every 3rd frame
            
            # Store last detected face locations and names
            last_face_locations = []
            last_recognized_names = []
            persist_frames = 10  # Number of frames to persist bounding boxes
            persist_counter = 0
            
            while True:
                success, frame = camera.read()
                if not success:
                    logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)  # Short delay before retrying
                    continue
                
                frame_count += 1
                
                # Process only every nth frame for better performance
                if frame_count % process_interval == 0:
                    # Recognize faces in the frame
                    face_locations, recognized_names = recognize_faces(
                        frame, 
                        self.known_face_encodings, 
                        self.known_face_names,
                        Config.FACE_RECOGNITION_TOLERANCE,
                        Config.FACE_RECOGNITION_MODEL
                    )
                    
                    # If faces are detected, update the last detected data
                    if face_locations:
                        last_face_locations = face_locations
                        last_recognized_names = recognized_names
                        persist_counter = persist_frames  # Reset persist counter
                    else:
                        # Decrease persist counter if no faces are detected
                        if persist_counter > 0:
                            persist_counter -= 1
                        else:
                            # Clear last detected data if persist counter reaches 0
                            last_face_locations = []
                            last_recognized_names = []
                    
                    # Log attendance for recognized people (with cooldown)
                    current_time = time.time()
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    for name in recognized_names:
                        if name != "Unknown":
                            # Check if we should log this person now
                            if (name not in self.last_log_time or 
                                current_time - self.last_log_time[name] > self.log_cooldown):
                                # Log attendance and update last log time
                                log_attendance(self.branch, name, today)
                                self.last_log_time[name] = current_time
                
                # Draw the last detected faces (persisted if necessary)
                self._draw_faces(frame, last_face_locations, last_recognized_names)
                
                # Convert the frame to JPEG format
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.warning("Failed to encode frame")
                    continue
                
                # Yield the frame as bytes
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        except Exception as e:
            logger.error(f"Error in video stream: {str(e)}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self._error_frame() + b'\r\n')
        
        finally:
            # Ensure camera is released
            if camera is not None:
                camera.release()
    
    def _draw_faces(self, frame, face_locations, recognized_names):
        """Draw rectangles and names for recognized faces."""
        for (top, right, bottom, left), name in zip(face_locations, recognized_names):
            # Different colors for known vs unknown faces
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Draw rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Create a filled rectangle for the name label
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Put name text
            cv2.putText(
                frame, name, (left + 6, bottom - 6), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1
            )
    
    def _error_frame(self):
        """Generate an error frame when camera fails."""
        # Create a black frame with error message
        frame = np.zeros((480, 640, 3), np.uint8)
        cv2.putText(
            frame, "Camera Error", (200, 240),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()