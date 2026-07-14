# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
#from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from datetime import datetime
import pandas as pd
import functools

# Custom modules
from attendance_manager import AttendanceManager
from database import init_db, get_db
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Session
Session(app)

# Initialize CSRF protection
#csrf = CSRFProtect(app)

# Initialize database connection
init_db()

def load_branch_data():
    """Load branch data with encrypted passwords and roles."""
    branches = {
        "CSM": {
            "branch_name": "Computer Science Main",
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

def is_admin(branch_id, user_id):
    """Check if user is an admin for the branch."""
    branches = load_branch_data()
    if branch_id in branches and user_id in branches[branch_id]["roles"]:
        return branches[branch_id]["roles"][user_id]["role"] in ["cr", "teacher"]
    return False

def is_student(branch_id, user_id):
    """Check if user is a student for the branch."""
    branches = load_branch_data()
    if branch_id in branches and user_id in branches[branch_id]["roles"]:
        return branches[branch_id]["roles"][user_id]["role"] == "student"
    return False

def admin_required(f):
    """Decorator to ensure user is admin or teacher."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'branch_id' not in session or 'user_id' not in session:
            return redirect(url_for('login'))
        if not is_admin(session['branch_id'], session['user_id']):
            flash("You don't have admin privileges", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorator to ensure user is logged in."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'branch_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def utility_processor():
    def count_member_images(branch_id, name):
        person_folder = os.path.join("data", branch_id, name)
        if os.path.exists(person_folder):
            return len([f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        return 0
    return dict(count_member_images=count_member_images, is_admin=is_admin)

@app.route('/')
@login_required
def index():
    """Render the home page with video feed."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication."""
    if request.method == 'POST':
        branch_id = request.form.get('branch_id')
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        branches = load_branch_data()
        
        if branch_id in branches and user_id in branches[branch_id]["roles"]:
            stored_pw = branches[branch_id]["roles"][user_id]["password"]
            if check_password_hash(stored_pw, password):
                session.permanent = True
                session['branch_id'] = branch_id
                session['user_id'] = user_id
                
                # Initialize attendance for the branch
                initialize_attendance(branch_id)
                
                # Redirect based on role
                user_role = branches[branch_id]["roles"][user_id]["role"]
                if user_role in ["cr", "teacher"]:
                    logger.info(f"Admin login: {user_id} for branch {branch_id}")
                    return redirect(url_for('admin_dashboard'))
                elif user_role == "student":
                    logger.info(f"Student login: {user_id} for branch {branch_id}")
                    return redirect(url_for('index'))
                
                flash('Invalid role', 'error')
                logger.warning(f"Invalid role for user: {user_id} in branch: {branch_id}")
                return redirect(url_for('login'))
            else:
                flash('Invalid credentials', 'error')
                logger.warning(f"Failed login attempt for branch: {branch_id}")
        else:
            flash('Invalid branch ID or user ID', 'error')
            logger.warning(f"Login attempt with unknown branch ID or user ID: {branch_id}, {user_id}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out the current user."""
    branch_id = session.pop('branch_id', None)
    user_id = session.pop('user_id', None)
    if branch_id:
        logger.info(f"User logged out: {user_id} from branch {branch_id}")
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/video_feed')
@login_required
def video_feed():
    """Stream video feed with face recognition."""
    branch = session['branch_id']
    try:
        return Response(
            AttendanceManager(branch).generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Error in video feed: {str(e)}")
        return Response(status=500)

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    """Display and filter attendance records."""
    branch = session['branch_id']
    user_id = session['user_id']

    if not is_student(branch, user_id):
        flash("Only students can mark attendance.", "error")
        return redirect(url_for('index'))

    try:
        if request.method == 'POST':
            date = request.form.get('date', datetime.now().strftime("%Y-%m-%d"))
        else:
            date = datetime.now().strftime("%Y-%m-%d")

        db = get_db()
        records = list(db.attendance.find(
            {"branch": branch, "date": date},
            {"_id": 0}
        ))
        
        logger.info(f"Fetched {len(records)} attendance records for {branch} on {date}")
        return render_template('attendance.html', records=records, date=date)
    
    except Exception as e:
        logger.error(f"Error fetching attendance data: {str(e)}")
        flash('Error fetching attendance data.', 'error')
        return render_template('attendance.html', records=[], date=datetime.now().strftime("%Y-%m-%d"))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new person for face recognition."""
    branch = session['branch_id']

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            images = request.files.getlist('images')

            # Validate inputs
            if not name:
                flash("Name is required!", "error")
                return redirect(url_for('register'))

            if not images or all(image.filename == '' for image in images):
                flash("At least one image is required!", "error")
                return redirect(url_for('register'))

            # Create directory structure
            person_folder = os.path.join("data", branch, name)
            os.makedirs(person_folder, exist_ok=True)

            # Save uploaded images
            saved_images = 0
            for i, image in enumerate(images):
                if image.filename == '':
                    continue
                
                if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                image_path = os.path.join(person_folder, f"{name}_{i + 1}.jpg")
                image.save(image_path)
                saved_images += 1

            if saved_images == 0:
                flash("No valid images were uploaded.", "error")
                return redirect(url_for('register'))

            # Update class list
            update_class_list(branch, name)

            # Retrain the face recognition model
            from train_model import train_model
            train_model(branch)
            
            flash(f"{name} registered successfully with {saved_images} images!", "success")
            logger.info(f"New person registered: {name} in branch {branch} with {saved_images} images")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            flash(f"Registration failed: {str(e)}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/registered_persons')
@login_required
def registered_persons():
    """Display list of registered persons."""
    branch = session['branch_id']
    class_list_path = os.path.join("data", branch, "class_list.csv")
    
    try:
        if os.path.exists(class_list_path):
            class_list = pd.read_csv(class_list_path)["Name"].tolist()
        else:
            class_list = []
        
        return render_template('registered_persons.html', class_list=class_list)
    except Exception as e:
        logger.error(f"Error fetching registered persons: {str(e)}")
        flash("Error loading registered persons.", "error")
        return render_template('registered_persons.html', class_list=[])

@app.route('/delete/<name>', methods=['POST'])
@login_required
def delete(name):
    """Delete a registered person."""
    branch = session['branch_id']

    try:
        # Delete person's images
        person_folder = os.path.join("data", branch, name)
        if os.path.exists(person_folder):
            for file in os.listdir(person_folder):
                os.remove(os.path.join(person_folder, file))
            os.rmdir(person_folder)

        # Update class list
        class_list_path = os.path.join("data", branch, "class_list.csv")
        if os.path.exists(class_list_path):
            class_list = pd.read_csv(class_list_path)
            class_list = class_list[class_list["Name"] != name]
            class_list.to_csv(class_list_path, index=False)

        # Delete from database
        db = get_db()
        db.attendance.delete_many({"branch": branch, "name": name})

        # Retrain the model
        from train_model import train_model
        train_model(branch)
        
        logger.info(f"Person deleted: {name} from branch {branch}")
        flash(f"{name} deleted successfully!", "success")
    except Exception as e:
        logger.error(f"Error deleting person {name}: {str(e)}")
        flash(f"Error deleting {name}: {str(e)}", "error")
    
    return redirect(url_for('registered_persons'))

@app.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    """Display attendance analytics and charts."""
    branch = session['branch_id']

    try:
        # Handle date range filter
        start_date = request.form.get('start_date', datetime.now().replace(day=1).strftime("%Y-%m-%d"))  # Default to first day of current month
        end_date = request.form.get('end_date', datetime.now().strftime("%Y-%m-%d"))  # Default to today

        # Check for export request
        if request.form.get('export') == 'true':
            return export_attendance_csv(branch, start_date, end_date)
        
        # Fetch attendance data
        db = get_db()
        attendance_data = list(db.attendance.find({
            "branch": branch,
            "date": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}))

        # Process data for charts
        chart_data = process_analytics_data(attendance_data, branch)
        
        # Calculate additional statistics for summary cards
        total_days = len(chart_data['dates'])
        
        # Calculate average present percentage
        avg_present = 0
        if chart_data['attendance_percentage']:
            avg_present = round(sum(chart_data['attendance_percentage']) / len(chart_data['attendance_percentage']), 1)
        
        # Find most absent day (day with lowest attendance)
        most_absent_day = "N/A"
        best_day = "N/A"
        
        if chart_data['dates'] and chart_data['attendance_percentage']:
            min_attendance_idx = chart_data['attendance_percentage'].index(min(chart_data['attendance_percentage'])) if chart_data['attendance_percentage'] else -1
            max_attendance_idx = chart_data['attendance_percentage'].index(max(chart_data['attendance_percentage'])) if chart_data['attendance_percentage'] else -1
            
            if min_attendance_idx >= 0:
                most_absent_day = chart_data['dates'][min_attendance_idx]
            
            if max_attendance_idx >= 0:
                best_day = chart_data['dates'][max_attendance_idx]
        
        # Process weekly data
        weekly_data = process_weekly_data(attendance_data)
        
        return render_template(
            'analytics.html',
            dates=chart_data['dates'],
            present_count=chart_data['present_count'],
            absent_count=chart_data['absent_count'],
            attendance_percentage=chart_data['attendance_percentage'],
            weekly_data=weekly_data,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            avg_present=avg_present,
            most_absent_day=most_absent_day,
            best_day=best_day
        )
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        flash("Error generating analytics.", "error")
        return render_template(
            'analytics.html',
            dates=[],
            present_count=[],
            absent_count=[],
            attendance_percentage=[],
            weekly_data={"weeks": [], "percentages": []},
            start_date=datetime.now().replace(day=1).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
            total_days=0,
            avg_present=0,
            most_absent_day="N/A",
            best_day="N/A"
        )

def process_analytics_data(attendance_data, branch):
    """Process attendance data for charts."""
    # Sort data by date
    attendance_data.sort(key=lambda x: x.get('date', ''))
    
    # Group by date
    date_groups = {}
    for record in attendance_data:
        date = record.get('date')
        if date:
            if date not in date_groups:
                date_groups[date] = {'present': 0, 'absent': 0}
            
            if record.get('status') == 'Present':
                date_groups[date]['present'] += 1
            else:
                date_groups[date]['absent'] += 1
    
    # Prepare data for charts
    dates = list(date_groups.keys())
    present_count = [date_groups[date]['present'] for date in dates]
    absent_count = [date_groups[date]['absent'] for date in dates]
    
    # Calculate attendance percentage
    attendance_percentage = []
    for date in dates:
        total = date_groups[date]['present'] + date_groups[date]['absent']
        percentage = (date_groups[date]['present'] / total * 100) if total > 0 else 0
        attendance_percentage.append(round(percentage, 1))
    
    return {
        'dates': dates,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage
    }

def process_weekly_data(attendance_data):
    """Process attendance data for weekly comparison chart."""
    # Group data by week
    week_groups = {}
    
    for record in attendance_data:
        date_str = record.get('date')
        if not date_str:
            continue
            
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # Get the week number and year
            year = date_obj.isocalendar()[0]
            week = date_obj.isocalendar()[1]
            week_key = f"{year}-W{week:02d}"
            
            if week_key not in week_groups:
                week_groups[week_key] = {'present': 0, 'absent': 0}
            
            if record.get('status') == 'Present':
                week_groups[week_key]['present'] += 1
            else:
                week_groups[week_key]['absent'] += 1
        except ValueError:
            continue
    
    # Sort weeks chronologically
    sorted_weeks = sorted(week_groups.keys())
    
    # Calculate weekly percentages
    percentages = []
    for week in sorted_weeks:
        total = week_groups[week]['present'] + week_groups[week]['absent']
        percentage = (week_groups[week]['present'] / total * 100) if total > 0 else 0
        percentages.append(round(percentage, 1))
    
    return {
        'weeks': sorted_weeks,
        'percentages': percentages
    }

def export_attendance_csv(branch, start_date, end_date):
    """Export attendance data as CSV."""
    from flask import make_response
    import csv
    from io import StringIO
    
    # Fetch data
    db = get_db()
    attendance_data = list(db.attendance.find({
        "branch": branch,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}))
    
    # Create CSV
    output = StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(['Name', 'Date', 'Status', 'Time'])
    
    # Write data
    for record in sorted(attendance_data, key=lambda x: (x.get('date', ''), x.get('name', ''))):
        csv_writer.writerow([
            record.get('name', ''),
            record.get('date', ''),
            record.get('status', ''),
            record.get('timestamp', '').strftime('%H:%M:%S') if record.get('timestamp') else ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=attendance_{start_date}_to_{end_date}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    branch = session['branch_id']
    
    # Get today's attendance stats
    today = datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    
    # Get REAL recent activity from database
    recent_activity = list(db.attendance.find(
        {"branch": branch},
        {"_id": 0, "name": 1, "status": 1, "date": 1, "timestamp": 1}
    ).sort("timestamp", -1).limit(5))
    
    # Format the activity data
    formatted_activity = []
    for activity in recent_activity:
        formatted_activity.append({
            "time": activity["timestamp"].strftime("%I:%M %p"),
            "action": "Attendance Marked",
            "details": f"{activity['name']} marked {activity['status'].lower()}",
            "status": activity["status"]
        })
    
    
    # Calculate attendance stats
    today = datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    total_members = len(pd.read_csv(os.path.join("data", branch, "class_list.csv"))["Name"].tolist())
    present_count = db.attendance.count_documents({"branch": branch, "date": today, "status": "Present"})
    absent_count = total_members - present_count
    attendance_percentage = round((present_count / total_members) * 100, 2) if total_members > 0 else 0

    return render_template('admin_dashboard.html',
        present_count=present_count,
        absent_count=absent_count,
        attendance_percentage=attendance_percentage,
        total_members=total_members,
        recent_activity=formatted_activity
    )

@app.route('/admin/manage_members')
@admin_required
def manage_members():
    """Manage members page."""
    branch = session['branch_id']
    class_list_path = os.path.join("data", branch, "class_list.csv")
    
    try:
        if os.path.exists(class_list_path):
            class_list = pd.read_csv(class_list_path)["Name"].tolist()
        else:
            class_list = []
        
        return render_template('manage_members.html', class_list=class_list)
    except Exception as e:
        logger.error(f"Error fetching members: {str(e)}")
        flash("Error loading members.", "error")
        return render_template('manage_members.html', class_list=[])

@app.route('/admin/add_member', methods=['GET', 'POST'])
@admin_required
def add_member():
    """Add new member (admin version)."""
    branch = session['branch_id']

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            images = request.files.getlist('images')

            if not name:
                flash("Name is required!", "error")
                return redirect(url_for('add_member'))

            if not images or all(image.filename == '' for image in images):
                flash("At least one image is required!", "error")
                return redirect(url_for('add_member'))

            person_folder = os.path.join("data", branch, name)
            os.makedirs(person_folder, exist_ok=True)

            saved_images = 0
            for i, image in enumerate(images):
                if image.filename == '':
                    continue
                
                if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                image_path = os.path.join(person_folder, f"{name}_{i + 1}.jpg")
                image.save(image_path)
                saved_images += 1

            if saved_images == 0:
                flash("No valid images were uploaded.", "error")
                return redirect(url_for('add_member'))

            update_class_list(branch, name)

            from train_model import train_model
            train_model(branch)
            
            flash(f"{name} registered successfully with {saved_images} images!", "success")
            return redirect(url_for('manage_members'))
            
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            flash(f"Registration failed: {str(e)}", "error")
            return redirect(url_for('add_member'))

    return render_template('add_member.html')

@app.route('/admin/delete_member/<name>', methods=['POST'])
@admin_required
def delete_member(name):
    """Delete a member (admin version)."""
    branch = session['branch_id']

    try:
        # Delete person's images
        person_folder = os.path.join("data", branch, name)
        if os.path.exists(person_folder):
            for file in os.listdir(person_folder):
                os.remove(os.path.join(person_folder, file))
            os.rmdir(person_folder)

        # Update class list
        class_list_path = os.path.join("data", branch, "class_list.csv")
        if os.path.exists(class_list_path):
            class_list = pd.read_csv(class_list_path)
            class_list = class_list[class_list["Name"] != name]
            class_list.to_csv(class_list_path, index=False)

        # Delete from database
        db = get_db()
        db.attendance.delete_many({"branch": branch, "name": name})

        # Retrain the model
        from train_model import train_model
        train_model(branch)
        
        logger.info(f"Admin deleted member: {name} from branch {branch}")
        flash(f"{name} deleted successfully!", "success")
    except Exception as e:
        logger.error(f"Error deleting member {name}: {str(e)}")
        flash(f"Error deleting {name}: {str(e)}", "error")
    
    return redirect(url_for('manage_members'))

@app.route('/admin/manage_attendance')
@admin_required
def manage_attendance():
    """Manage attendance records."""
    branch = session['branch_id']
    
    # Get filter parameters
    date_filter = request.args.get('date', '')
    name_filter = request.args.get('name', '')
    status_filter = request.args.get('status', '')
    
    # Build query
    query = {"branch": branch}
    if date_filter:
        query["date"] = date_filter
    if name_filter:
        query["name"] = {"$regex": name_filter, "$options": "i"}
    if status_filter:
        query["status"] = status_filter
    
    db = get_db()
    records = list(db.attendance.find(
        query,
        {"_id": 0}
    ).sort("date", -1).limit(100))

    today_date_str = datetime.now().strftime('%Y-%m-%d')
    today_records = list(db.attendance.find(
        {"branch": branch, "date": today_date_str},
        {"_id": 0}
    ))
    today_total = len(today_records)
    today_present = sum(1 for record in today_records if record.get('status') == 'Present')
    today_absent = sum(1 for record in today_records if record.get('status') == 'Absent')
    today_date = datetime.now().strftime('%B %d, %Y')
    
    return render_template(
        'manage_attendance.html',
        records=records,
        today_date=today_date,
        today_total=today_total,
        today_present=today_present,
        today_absent=today_absent,
        today_date_str=today_date_str
    )

@app.route('/admin/edit_attendance', methods=['POST'])
@admin_required
def edit_attendance():
    """Edit attendance record."""
    branch = session['branch_id']
    name = request.form.get('name')
    date = request.form.get('date')
    status = request.form.get('status')
    
    if not all([name, date, status]):
        flash("Missing required fields", "error")
        return redirect(url_for('manage_attendance'))
    
    db = get_db()
    db.attendance.update_one(
        {"branch": branch, "name": name, "date": date},
        {"$set": {"status": status, "timestamp": datetime.now()}},
        upsert=True
    )
    
    flash(f"Attendance for {name} on {date} updated to {status}", "success")
    logger.info(f"Admin {session['user_id']} updated attendance for {name} on {date} to {status}")
    return redirect(url_for('manage_attendance'))

# Helper Functions
def update_class_list(branch, name):
    """Add a person to the class list CSV file."""
    class_list_path = os.path.join("data", branch, "class_list.csv")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(class_list_path), exist_ok=True)
    
    # Check if the file exists
    if not os.path.exists(class_list_path):
        # Create the file with a header
        with open(class_list_path, "w") as f:
            f.write("Name\n")
    
    # Read existing names to avoid duplicates
    try:
        class_list = pd.read_csv(class_list_path)
        if name not in class_list["Name"].values:
            # Append the new name to the CSV file
            with open(class_list_path, "a") as f:
                f.write(f"{name}\n")
    except Exception as e:
        logger.error(f"Error updating class list: {str(e)}")
        # If reading fails, create a new file with header and the name
        with open(class_list_path, "w") as f:
            f.write("Name\n")
            f.write(f"{name}\n")

def process_analytics_data(attendance_data, branch):
    """Process attendance data for analytics charts."""
    dates = []
    present_count = []
    absent_count = []

    # Group by date
    date_groups = {}
    for record in attendance_data:
        date = record["date"]
        if date not in date_groups:
            date_groups[date] = {"present": 0, "absent": 0}
        
        if record["status"] == "Present":
            date_groups[date]["present"] += 1
        else:
            date_groups[date]["absent"] += 1
    
    # Sort dates and extract counts
    sorted_dates = sorted(date_groups.keys())
    
    for date in sorted_dates:
        dates.append(date)
        present_count.append(date_groups[date]["present"])
        absent_count.append(date_groups[date]["absent"])
    
    # Calculate attendance percentage
    try:
        class_list_path = os.path.join("data", branch, "class_list.csv")
        if os.path.exists(class_list_path):
            total_students = len(pd.read_csv(class_list_path)["Name"].tolist())
        else:
            total_students = 0
            
        attendance_percentage = [
            round((present / total_students) * 100, 2) if total_students > 0 else 0
            for present in present_count
        ]
    except Exception:
        attendance_percentage = [0] * len(dates)
    
    return {
        "dates": dates,
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_percentage": attendance_percentage
    }

def initialize_attendance(branch):
    """Initialize attendance records for all registered users."""
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        class_list_path = os.path.join("data", branch, "class_list.csv")
        
        if os.path.exists(class_list_path):
            class_list = pd.read_csv(class_list_path)["Name"].tolist()
            db = get_db()
            
            for name in class_list:
                existing_record = db.attendance.find_one({
                    "branch": branch,
                    "name": name,
                    "date": date
                })
                
                if not existing_record:
                    db.attendance.insert_one({
                        "branch": branch,
                        "name": name,
                        "date": date,
                        "status": "Absent",
                        "timestamp": datetime.now()
                    })
                    logger.debug(f"Initialized attendance for {name} in {branch} on {date}")
    except Exception as e:
        logger.error(f"Error initializing attendance: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting application on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)