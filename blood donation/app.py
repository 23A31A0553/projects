from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.distance import geodesic
from datetime import datetime, date
from models import db, User, Admin, BloodRequest, DonationHistory, ChatMessage, Hospital, AuditLog, SystemSettings, AIConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lifelink_secret_key_change_in_production'
import os
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'lifelink.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Check for namespaced IDs
    if user_id.startswith('admin_'):
        try:
            uid = int(user_id.split('_')[1])
            return db.session.get(Admin, uid)
        except (IndexError, ValueError):
            return None
            
    if user_id.startswith('user_'):
        try:
            uid = int(user_id.split('_')[1])
            user = db.session.get(User, uid)
            if user and not user.is_approved:
                return None # Block login if not approved
            return user
        except (IndexError, ValueError):
            return None

    # Fallback for legacy/numeric IDs (default to User first to maintain some backward compat if needed, 
    # though valid sessions should now have prefixes)
    try:
        max_legacy_check = int(user_id)
        user = db.session.get(User, max_legacy_check)
        if user:
            if not user.is_approved: return None
            return user
        return db.session.get(Admin, max_legacy_check)
    except ValueError:
        return None

# --- HELPER: Smart Matching Logic ---
def calculate_match_score(donor, request_lat, request_lon):
    """
    Match Score = 
    (Location Closeness * 40) + 
    (Recency * 30) + 
    (Health Score * 30)
    """
    # 1. Location (Max 40)
    donor_loc = (donor.latitude, donor.longitude)
    req_loc = (request_lat, request_lon)
    try:
        distance = geodesic(donor_loc, req_loc).km
    except:
        distance = 1000

    # Score decreases as distance increases. Max score for < 1km.
    # 50km radius consideration
    location_score = max(0, 40 - (distance * 0.8))

    # 2. Recency (Max 30)
    # Prefer donors who haven't donated in a long time
    if donor.last_donation_date:
        days_diff = (date.today() - donor.last_donation_date).days
    else:
        days_diff = 365 
        
    if days_diff < 90:
        return 0, distance # Blocked

    recency_score = min(30, (days_diff / 180) * 30)

    # 3. Health Score (Max 30)
    health_deduction = 0
    if donor.smoking: health_deduction += 10
    if donor.drinking: health_deduction += 10
    health_score = max(0, 30 - health_deduction)

    total_score = location_score + recency_score + health_score
    return round(total_score, 2), round(distance, 2)

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test')
def test_frontend():
    return "<h1>Backend is active</h1><p>If you see this, Flask is working.</p>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        mobile = request.form.get('mobile_number')
        password = request.form.get('password')
        blood_group = request.form.get('blood_group')
        age = request.form.get('age')
        city = request.form.get('city')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        
        # Health
        bp = 1 if request.form.get('bp') else 0
        sugar = 1 if request.form.get('sugar') else 0
        heart = 1 if request.form.get('heart_disease') else 0
        asthma = 1 if request.form.get('asthma') else 0
        smoking = 1 if request.form.get('smoking') else 0
        drinking = 1 if request.form.get('drinking') else 0
        
        last_donation = request.form.get('last_donation_date')
        
        # Validation
        if User.query.filter_by(mobile_number=mobile).first():
            return render_template('register.html', error="Mobile number already exists.")
            
        # Create User
        new_user = User(
            full_name=full_name, mobile_number=mobile, 
            password_hash=generate_password_hash(password),
            blood_group=blood_group, age=age, city=city,
            latitude=float(lat), longitude=float(lon),
            bp=bp, sugar=sugar, heart_disease=heart, asthma=asthma,
            smoking=smoking, drinking=drinking,
            last_donation_date=datetime.strptime(last_donation, '%Y-%m-%d').date() if last_donation else None
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile_number')
        password = request.form.get('password')
        
        user = User.query.filter_by(mobile_number=mobile).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_approved:
                return render_template('login.html', error="Account pending approval.")
            login_user(user)
            check_eligibility(user) # Auto-update status
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    logout_user()
    return redirect(url_for('home'))

def check_eligibility(user):
    if not user.last_donation_date:
        user.is_available = True
        return
        
    days_diff = (date.today() - user.last_donation_date).days
    if days_diff >= 90:
        user.is_available = True
    else:
        user.is_available = False
    db.session.commit()

@app.route('/my-history')
@login_required
def my_history():
    history = DonationHistory.query.filter_by(donor_id=current_user.id).order_by(DonationHistory.donation_date.desc()).all()
    return render_template('history.html', history=history)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.age = request.form.get('age')
        current_user.city = request.form.get('city')
        current_user.blood_group = request.form.get('blood_group')
        # Health updates
        current_user.smoking = 'smoking' in request.form
        current_user.drinking = 'drinking' in request.form
        current_user.bp = 'bp' in request.form
        current_user.sugar = 'sugar' in request.form
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=current_user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pass = request.form.get('current_password')
        new_pass = request.form.get('new_password')
        
        if check_password_hash(current_user.password_hash, current_pass):
            current_user.password_hash = generate_password_hash(new_pass)
            db.session.commit()
            flash('Password changed successfully!')
            return redirect(url_for('profile'))
        else:
            flash('Incorrect current password!')
            
    return render_template('change_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Admin):
        return redirect(url_for('admin_dashboard'))
    
    my_requests = BloodRequest.query.filter_by(requester_id=current_user.id).all()
    
    # Fetch requests near me (or just all active ones for now)
    # Exclude my own requests
    nearby_requests = BloodRequest.query.filter(
        BloodRequest.requester_id != current_user.id,
        BloodRequest.status == 'Pending'
    ).order_by(BloodRequest.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', user=current_user, requests=my_requests, nearby_requests=nearby_requests)

@app.route('/request-blood', methods=['GET', 'POST'])
@login_required
def request_blood():
    if request.method == 'POST':
        req = BloodRequest(
            requester_id=current_user.id,
            patient_name=request.form.get('patient_name'),
            blood_group=request.form.get('blood_group'),
            hospital_name=request.form.get('hospital_name'),
            hospital_location=request.form.get('hospital_location'),
            req_latitude=float(request.form.get('req_latitude')),
            req_longitude=float(request.form.get('req_longitude')),
            urgency_level=request.form.get('urgency_level'),
            contact_number=request.form.get('contact_number')
        )
        db.session.add(req)
        db.session.commit()
        return redirect(url_for('find_donors', req_id=req.id))
        
    return render_template('request.html')

@app.route('/find-donors')
@login_required
def find_donors():
    req_id = request.args.get('req_id')
    req = BloodRequest.query.get_or_404(req_id)
    
    # Filter Logic
    target_bg = req.blood_group
    search_bgs = [target_bg]
    if target_bg != 'O-':
        search_bgs.append('O-')
        
    candidates = User.query.filter(User.blood_group.in_(search_bgs), User.is_available==True).all()
    
    ranked = []
    for donor in candidates:
        if donor.id == current_user.id: continue # Don't suggest self
        
        score, dist = calculate_match_score(donor, req.req_latitude, req.req_longitude)
        if score > 0:
            donor.score = score
            donor.distance = dist
            donor.match_color = 'green' if score > 80 else 'orange'
            ranked.append(donor)
            
    ranked.sort(key=lambda x: x.score, reverse=True)
    return render_template('donors.html', donors=ranked[:5], blood_request=req)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        # For first run, create admin if not exists
        if not admin and username == 'admin' and password == 'admin123':
            admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid Admin Credentials")
            
    return render_template('admin_login.html')

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        return redirect(url_for('dashboard'))
        
    donors = User.query.all()
    requests = BloodRequest.query.all()
    fulfilled_count = BloodRequest.query.filter_by(status='Fulfilled').count()
    return render_template('admin/dashboard.html', donors=donors, requests=requests, helped=fulfilled_count)

# --- AUDIT LOG HELPER ---
def log_action(action, details=None):
    if current_user.is_authenticated and isinstance(current_user, Admin):
        log = AuditLog(
            admin_id=current_user.id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

# --- ADMIN DONOR MANAGEMENT ---

@app.route('/admin/donors')
@login_required
def admin_donors():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    donors = User.query.all()
    return render_template('admin/donors.html', donors=donors)

@app.route('/admin/block-user/<int:user_id>/<action>')
@login_required
def block_user(user_id, action):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    user = User.query.get_or_404(user_id)
    if action == 'block':
        user.is_approved = False
        user.is_available = False
        user.is_locked = True
        log_action('BLOCK_USER', f'Blocked user {user.full_name} ({user.id})')
    elif action == 'unblock':
        user.is_approved = True
        user.is_locked = False
        log_action('UNBLOCK_USER', f'Unblocked user {user.full_name} ({user.id})')
    db.session.commit()
    return redirect(url_for('admin_donors'))

@app.route('/admin/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    user = User.query.get_or_404(user_id)
    name = user.full_name
    
    # Cascade Delete: Remove related records first
    DonationHistory.query.filter_by(donor_id=user.id).delete()
    ChatMessage.query.filter((ChatMessage.sender_id==user.id) | (ChatMessage.receiver_id==user.id)).delete()
    # Requests will set requester_id to NULL automatically if configured, or we can leave them
    # For cleanliness, we should probably keep requests but show "Unknown User" or leave as is.
    
    db.session.delete(user)
    db.session.commit()
    log_action('DELETE_USER', f'Deleted user {name} ({user_id})')
    return redirect(url_for('admin_donors'))

@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    user = User.query.get_or_404(user_id)
    new_pass = request.form.get('new_password')
    if new_pass:
        user.password_hash = generate_password_hash(new_pass)
        db.session.commit()
        log_action('RESET_PASSWORD', f'Reset password for user {user.full_name}')
        flash(f'Password reset for {user.full_name}')
    return redirect(url_for('admin_donors'))

# --- ADMIN REQUEST MANAGEMENT ---

@app.route('/admin/requests')
@login_required
def admin_requests():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    reqs = BloodRequest.query.order_by(BloodRequest.created_at.desc()).all()
    donors = User.query.filter_by(is_available=True, is_approved=True).all()
    return render_template('admin/requests.html', requests=reqs, donors=donors)

@app.route('/admin/update-request/<int:req_id>', methods=['POST'])
@login_required
def update_request(req_id):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    req = BloodRequest.query.get_or_404(req_id)
    status = request.form.get('status')
    if status and status != req.status:
        old_status = req.status
        req.status = status
        db.session.commit()
        log_action('UPDATE_REQUEST', f'Changed request {req_id} status from {old_status} to {status}')
    return redirect(url_for('admin_requests'))

@app.route('/admin/assign-donor/<int:req_id>', methods=['POST'])
@login_required
def assign_donor(req_id):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    # In a real app, this would notify the donor. 
    # For now, we just log it as an admin action "matching" a donor manually.
    donor_id = request.form.get('donor_id')
    if donor_id:
        try:
            donor = User.query.get(int(donor_id))
            if donor:
                log_action('ASSIGN_DONOR', f'Assigned donor {donor.full_name} to request {req_id}')
                flash(f'Assigned {donor.full_name} to request')
        except (ValueError, TypeError):
            flash('Invalid Donor Selection', 'error')
            
    return redirect(url_for('admin_requests'))

# --- ADMIN ADVANCED MODULES ---

@app.route('/admin/audit-logs')
@login_required
def admin_audit_logs():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)

# Include manage_hospitals route (refactored to new template location)
@app.route('/admin/hospitals')
@login_required
def manage_hospitals():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    hospitals = Hospital.query.all()
    return render_template('admin/manage_hospitals.html', hospitals=hospitals)

@app.route('/admin/add-hospital', methods=['POST'])
@login_required
def add_hospital():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    name = request.form.get('name')
    city = request.form.get('city')
    address = request.form.get('address')
    contact = request.form.get('contact')
    Hospital.query.filter_by(name=name).first() # Check duplicate?
    
    h = Hospital(name=name, city=city, address=address, contact=contact)
    db.session.add(h)
    db.session.commit()
    log_action('ADD_HOSPITAL', f'Added hospital {name}')
    return redirect(url_for('manage_hospitals'))

@app.route('/admin/delete-hospital/<int:h_id>')
@login_required
def delete_hospital(h_id):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    h = Hospital.query.get_or_404(h_id)
    name = h.name
    db.session.delete(h)
    db.session.commit()
    log_action('DELETE_HOSPITAL', f'Deleted hospital {name}')
    return redirect(url_for('manage_hospitals'))

@app.route('/admin/forecast')
@login_required
def admin_forecast():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    # ... (existing forecast logic)
    predictions = {'A+': 'High Demand', 'O+': 'Critical', 'B+': 'Stable', 'AB-': 'Low'}
    trend = [10, 15, 8, 12, 20, 25] # Mock
    return render_template('admin/forecast.html', predictions=predictions, trend=trend)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings() # Create default if not exists
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        settings.donation_gap_days = int(request.form.get('donation_gap'))
        settings.emergency_radius_km = float(request.form.get('radius'))
        settings.admin_contact_email = request.form.get('email')
        db.session.commit()
        log_action('UPDATE_SETTINGS', 'Updated system configuration')
        flash('Settings updated!')
    
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/ai-control', methods=['GET', 'POST'])
@login_required
def admin_ai_control():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    ai_config = AIConfig.query.first()
    if not ai_config:
        ai_config = AIConfig()
        db.session.add(ai_config)
        db.session.commit()
        
    if request.method == 'POST':
        ai_config.weight_blood_group = float(request.form.get('w_bg'))
        ai_config.weight_distance = float(request.form.get('w_dist'))
        ai_config.weight_recency = float(request.form.get('w_rec'))
        ai_config.weight_health = float(request.form.get('w_h'))
        db.session.commit()
        log_action('UPDATE_AI', 'Updated AI matching weights')
        flash('AI Strategy Updated!')
        
    return render_template('admin/ai_control.html', config=ai_config)

@app.route('/admin/communication', methods=['GET', 'POST'])
@login_required
def admin_communication():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    return render_template('admin/communication.html')

@app.route('/admin/send-broadcast', methods=['POST'])
@login_required
def send_broadcast():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    msg = request.form.get('message')
    channel = request.form.get('channel') # SMS, WhatsApp, Dashboard
    
    # Simulate sending
    details = f"Sent {channel} broadcast: {msg[:20]}..."
    log_action('BROADCAST_SEND', details)
    session['emergency_alert'] = msg if channel == 'Dashboard' else None
    
    flash(f'{channel} Broadcast Sent Successfully!')
    return redirect(url_for('admin_communication'))

@app.route('/admin/monitoring')
@login_required
def admin_monitoring():
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    # Simulating online users (in production, use Redis/LastActive)
    online_donors = User.query.filter_by(is_available=True).limit(5).all() 
    active_emergencies = BloodRequest.query.filter_by(urgency_level='High', status='Pending').all()
    return render_template('admin/monitoring.html', online=online_donors, emergencies=active_emergencies)

@app.route('/admin/export/<type>')
@login_required
def admin_export(type):
    if not isinstance(current_user, Admin): return "Unauthorized", 403
    import csv
    from io import StringIO
    from flask import make_response
    
    si = StringIO()
    cw = csv.writer(si)
    
    if type == 'donors':
        cw.writerow(['ID', 'Name', 'Mobile', 'Blood Group', 'City'])
        rows = User.query.all()
        for r in rows: cw.writerow([r.id, r.full_name, r.mobile_number, r.blood_group, r.city])
        filename = 'donors.csv'
    elif type == 'requests':
        cw.writerow(['ID', 'Patient', 'Group', 'Status', 'Date'])
        rows = BloodRequest.query.all()
        for r in rows: cw.writerow([r.id, r.patient_name, r.blood_group, r.status, r.created_at])
        filename = 'requests.csv'
    elif type == 'logs':
        cw.writerow(['Time', 'Action', 'Admin', 'Details', 'IP'])
        rows = AuditLog.query.all()
        for r in rows: cw.writerow([r.timestamp, r.action, r.admin_id, r.details, r.ip_address])
        filename = 'audit_logs.csv'
    else:
        return "Invalid Export Type", 400
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output

# --- CHAT & CALL ROUTES (Restored) ---
    return jsonify(msgs_data)

# --- ADMIN ROUTES ENHANCEMENTS ---

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not isinstance(current_user, Admin):
        return "Unauthorized", 403
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.mobile_number = request.form.get('mobile_number')
        new_pass = request.form.get('password')
        if new_pass:
            user.password_hash = generate_password_hash(new_pass)
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
        
    return render_template('edit_user.html', user=user)

# Database Initialization
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
