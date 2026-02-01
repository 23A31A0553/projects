import logging
import sys
from app import app, db, User, Admin, BloodRequest, DonationHistory, ChatMessage
from werkzeug.security import generate_password_hash
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def verify_fixes():
    logging.info("Starting verification of Admin Fixes...")
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Setup Admin
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
                db.session.add(admin)
                db.session.commit()
            
            # Login Admin
            client.post('/admin-login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
            
            # --- Test 1: Forecast Page Syntax ---
            logging.info("Test 1: Forecast Page Load")
            resp = client.get('/admin/forecast')
            if resp.status_code == 200:
                logging.info("SUCCESS: Forecast page loaded (Syntax Fixed)")
            else:
                logging.error(f"FAILURE: Forecast page returned {resp.status_code}")
                logging.error(resp.data[:500]) # Log error head

            # --- Test 2: User Deletion with Dependencies ---
            logging.info("Test 2: User Deletion with Dependencies")
            # Create dummy user
            user = User(full_name='DeleteMe', mobile_number='9999999999', password_hash='x', 
                        blood_group='A+', age=20, city='X', latitude=0, longitude=0)
            db.session.add(user)
            db.session.commit()
            
            # Add dependency (History)
            hist = DonationHistory(donor_id=user.id, donation_date=datetime.date.today())
            db.session.add(hist)
            db.session.commit()
            
            # Try Delete
            del_resp = client.get(f'/admin/delete-user/{user.id}', follow_redirects=True)
            if del_resp.status_code == 200 and not User.query.get(user.id):
                logging.info("SUCCESS: User deleted successfully (Dependencies handled)")
            else:
                logging.error("FAILURE: User not deleted or error occurred")
                if User.query.get(user.id): logging.error("User still exists in DB")
            
            # --- Test 3: Manage Hospitals ---
            logging.info("Test 3: Manage Hospitals Page")
            hosp_resp = client.get('/admin/hospitals')
            if hosp_resp.status_code == 200:
                 logging.info("SUCCESS: Manage Hospitals page loaded")
            else:
                 logging.error(f"FAILURE: Manage Hospitals page returned {hosp_resp.status_code}")

            # --- Test 4: Assign Donor / Updates ---
            logging.info("Test 4: Request Updates")
            # Create dummy request
            req = BloodRequest(patient_name='Test', blood_group='A+', hospital_name='H', 
                               req_latitude=0, req_longitude=0, contact_number='1', urgency_level='High')
            db.session.add(req)
            db.session.commit()
            
            # Test Bad Assignment (Invalid ID)
            assign_resp = client.post(f'/admin/assign-donor/{req.id}', data={'donor_id': 'invalid'}, follow_redirects=True)
            if assign_resp.status_code == 200:
                logging.info("SUCCESS: Invalid assignment handled gracefully")
            else:
                 logging.error("FAILURE: Invalid assignment caused crash")

if __name__ == "__main__":
    verify_fixes()
