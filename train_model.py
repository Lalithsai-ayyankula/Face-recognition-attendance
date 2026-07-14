# train_model.py
import os
import cv2
import face_recognition
import pickle
import logging
import concurrent.futures
from datetime import datetime
from config import Config
import sys

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("train_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_image(args):
    """
    Process a single image to extract face encodings.
    Designed to be used with concurrent processing.
    
    Args:
        args: Tuple containing (image_path, person_name)
        
    Returns:
        tuple: Person name and encoding (or None if processing failed)
    """
    img_path, person_name = args
    
    try:
        # Load the image
        image = cv2.imread(img_path)
        if image is None:
            logger.warning(f"Unable to load image {img_path}. Skipping.")
            return person_name, None
        
        # Convert to RGB (face_recognition uses RGB)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect face locations using the configured model
        face_locations = face_recognition.face_locations(
            rgb_image, 
            model=Config.FACE_RECOGNITION_MODEL
        )
        
        if not face_locations:
            logger.warning(f"No face detected in {img_path}. Skipping.")
            return person_name, None
            
        # Detect face encodings
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        # Check if face was detected
        if not face_encodings:
            logger.warning(f"No face encodings generated for {img_path}. Skipping.")
            return person_name, None
        
        # Return the first face encoding (assuming one face per image)
        logger.debug(f"Successfully processed image {img_path}")
        return person_name, face_encodings[0]
    except Exception as e:
        logger.error(f"Error processing image {img_path}: {e}")
        return person_name, None

def train_model(branch_id):
    """
    Train the facial recognition model using images from the configured directory.
    Processes all images in parallel for better performance.
    
    Args:
        branch_id (str): Branch identifier
        
    Returns:
        str: Path to the saved model file
    """
    logger.info("Starting model training")
    start_time = datetime.now()
    
    # Get the training data directory from config
    training_dir = os.path.join(Config.DATA_DIR, branch_id)
    
    if not os.path.exists(training_dir):
        logger.error(f"Training directory not found: {training_dir}")
        os.makedirs(training_dir, exist_ok=True)
        logger.info(f"Created training directory: {training_dir}")
        return None
    
    # Dictionary to store face encodings for each person
    encodings = {}
    image_paths = []
    
    # Collect all image paths organized by person
    for person_name in os.listdir(training_dir):
        person_dir = os.path.join(training_dir, person_name)
        if not os.path.isdir(person_dir):
            continue
            
        for image_name in os.listdir(person_dir):
            ext = image_name.lower().split('.')[-1]
            if ext in Config.ALLOWED_EXTENSIONS:
                img_path = os.path.join(person_dir, image_name)
                image_paths.append((img_path, person_name))
    
    logger.info(f"Found {len(image_paths)} images to process")
    
    if not image_paths:
        logger.warning("No training images found. Please add images to the training directory.")
        return None
    
    # Process images in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(process_image, image_paths)
        
        for person_name, encoding in results:
            if encoding is not None:
                if person_name not in encodings:
                    encodings[person_name] = []
                encodings[person_name].append(encoding)
    
    # Check if we have valid encodings
    valid_encodings = {name: encs for name, encs in encodings.items() if encs}
    total_faces = sum(len(encs) for encs in valid_encodings.values())
    
    if not valid_encodings:
        logger.error("No valid face encodings found. Training failed.")
        return None
    
    logger.info(f"Successfully encoded {total_faces} faces for {len(valid_encodings)} people")
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(Config.DATA_DIR, branch_id)
    os.makedirs(models_dir, exist_ok=True)
    
    # Save the encodings to a pickle file
    output_path = os.path.join(models_dir, f"face_encodings_{branch_id}.pkl")
    
    with open(output_path, 'wb') as f:
        pickle.dump(
            {
                "encodings": [enc for enc_list in valid_encodings.values() for enc in enc_list],
                "names": [name for name in valid_encodings.keys() for _ in range(len(valid_encodings[name]))]
            },
            f
        )
    
    elapsed_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Model training completed in {elapsed_time:.2f} seconds")
    logger.info(f"Model saved to {output_path}")
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python train_model.py <branch_id>")
        sys.exit(1)
    
    branch_id = sys.argv[1]
    logger.info(f"Training model for branch: {branch_id}")
    model_path = train_model(branch_id)
    if model_path:
        logger.info(f"Training successful. Model saved at: {model_path}")
    else:
        logger.error("Training failed")