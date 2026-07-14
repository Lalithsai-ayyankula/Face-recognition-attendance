from flask import session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import functools

logger = logging.getLogger(__name__)

def load_branch_data():
    """Load branch data with encrypted passwords and roles."""
    branches = {
        "CSM": {
            "branch_name": "Computer Science Machine Learning",
            "password": generate_password_hash("csm123"),
            "roles": {
                "csmCR": {"password": generate_password_hash("csmCR123"), "role": "cr"},
                "csmTeacher": {"password": generate_password_hash("teacher123"), "role": "teacher"},
                "csmStudent": {"password": generate_password_hash("student123"), "role": "student"}
            }
        },
        "CAI": {
            "branch_name": "Computer Science AI",
            "password": generate_password_hash("cai123"),
            "roles": {
                "caiCR": {"password": generate_password_hash("caiCR123"), "role": "cr"},
                "caiTeacher": {"password": generate_password_hash("teacher123"), "role": "teacher"},
                "caiStudent": {"password": generate_password_hash("student123"), "role": "student"}
            }
        },
        "CSC": {
            "branch_name": "Computer Science Data",
            "password": generate_password_hash("csc123"),
            "roles": {
                "cscCR": {"password": generate_password_hash("cscCR123"), "role": "cr"},
                "cscTeacher": {"password": generate_password_hash("teacher123"), "role": "teacher"},
                "cscStudent": {"password": generate_password_hash("student123"), "role": "student"}
            }
        },
        "AID": {
            "branch_name": "Artificial Intelligence",
            "password": generate_password_hash("aid123"),
            "roles": {
                "aidCR": {"password": generate_password_hash("aidCR123"), "role": "cr"},
                "aidTeacher": {"password": generate_password_hash("teacher123"), "role": "teacher"},
                "aidStudent": {"password": generate_password_hash("student123"), "role": "student"}
            }
        }
    }
    return branches

def get_user_role(branch_id, user_id):
    """Get user role if credentials are valid."""
    branches = load_branch_data()
    if branch_id in branches:
        if user_id in branches[branch_id]["roles"]:
            return branches[branch_id]["roles"][user_id]["role"]
    return None

def check_credentials(branch_id, user_id, password):
    """Verify login credentials."""
    branches = load_branch_data()
    if branch_id in branches:
        if user_id in branches[branch_id]["roles"]:
            stored_pw = branches[branch_id]["roles"][user_id]["password"]
            return check_password_hash(stored_pw, password)
    return False

def require_role(required_role):
    """Decorator to check user role."""
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if 'branch_id' not in session or 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_role = get_user_role(session['branch_id'], session['user_id'])
            if user_role != required_role:
                flash("You don't have permission to access this page", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return wrapped
    return decorator