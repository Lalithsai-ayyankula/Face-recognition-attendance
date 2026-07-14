# database.py
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging
from functools import wraps
from config import Config
import datetime

logger = logging.getLogger(__name__)

# Global client connection
_client = None
_db = None

def init_db():
    """Initialize the database connection."""
    global _client, _db
    try:
        _client = MongoClient(Config.MONGO_URI, maxPoolSize=50)
        _db = _client[Config.MONGO_DB]
        # Test connection
        _db.command('ping')
        logger.info(f"Connected to MongoDB at {Config.MONGO_URI}")
        return True
    except PyMongoError as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False

def get_db():
    """Get the database connection."""
    global _db
    if _db is None:
        init_db()
    return _db

def db_operation(func):
    """Decorator for database operations with error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PyMongoError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            return None
    return wrapper

@db_operation
def log_attendance(branch, name, date, status="Present"):
    """Log or update attendance record."""
    db = get_db()
    existing_record = db.attendance.find_one({
        "branch": branch,
        "name": name,
        "date": date
    })
    
    if existing_record:
        if existing_record["status"] != status:
            db.attendance.update_one(
                {"_id": existing_record["_id"]},
                {"$set": {"status": status}}
            )
            logger.info(f"Updated attendance for {name} in {branch} on {date} to {status}")
    else:
        db.attendance.insert_one({
            "branch": branch,
            "name": name,
            "date": date,
            "status": status,
            "timestamp": datetime.now()
        })
        logger.info(f"Logged attendance for {name} in {branch} on {date}: {status}")
    
    return True