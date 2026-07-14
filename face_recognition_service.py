# face_recognition_service.py
import face_recognition
import cv2
import pickle
import os
import numpy as np
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

def load_encodings(branch_id):
    """
    Load face encodings for a specific branch.
    
    Args:
        branch_id (str): Branch identifier
        
    Returns:
        tuple: Lists of encodings and corresponding names
    """
    try:
        encoding_file = os.path.join(Config.DATA_DIR, branch_id, f"face_encodings_{branch_id}.pkl")
        
        # Check if encodings file exists
        if not os.path.exists(encoding_file):
            logger.warning(f"No encodings file found for branch {branch_id}.")
            return [], []
        
        # Load encodings from pickle file
        with open(encoding_file, "rb") as f:
            data = pickle.load(f)
            
        encodings = data.get("encodings", [])
        names = data.get("names", [])
        
        logger.info(f"Loaded {len(encodings)} face encodings for branch {branch_id}")
        return encodings, names
    
    except Exception as e:
        logger.error(f"Error loading encodings for branch {branch_id}: {str(e)}")
        return [], []

def recognize_faces(frame, known_face_encodings, known_face_names, tolerance=0.6, model="hog"):
    """
    Recognize faces in a video frame.
    
    Args:
        frame: Video frame (OpenCV format)
        known_face_encodings: List of known face encodings
        known_face_names: List of names corresponding to encodings
        tolerance: Face recognition tolerance (lower = stricter)
        model: Face detection model ('hog' or 'cnn')
        
    Returns:
        tuple: Face locations and corresponding names
    """
    # If no known faces, return empty results
    if not known_face_encodings:
        return [], []
    
    try:
        # Resize frame for faster processing
        scale = 0.25
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        
        # Convert to RGB (face_recognition uses RGB)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in the frame
        face_locations = face_recognition.face_locations(rgb_small_frame, model=model)
        
        # No faces found
        if not face_locations:
            return [], []
        
        # Get face encodings for found faces
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        recognized_names = []
        
        # Compare each face with known faces
        for face_encoding in face_encodings:
            # Compare the face with known faces
            matches = face_recognition.compare_faces(
                known_face_encodings, face_encoding, tolerance=tolerance
            )
            
            name = "Unknown"
            
            # Use face distance to find the best match
            if True in matches:
                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
            
            recognized_names.append(name)
        
        # Scale face locations back to original frame size
        face_locations = [
            (int(top/scale), int(right/scale), int(bottom/scale), int(left/scale))
            for (top, right, bottom, left) in face_locations
        ]
        
        return face_locations, recognized_names
        
    except Exception as e:
        logger.error(f"Error in face recognition: {str(e)}")
        return [], []