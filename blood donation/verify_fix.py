import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

try:
    from app import app, db, User, Admin
    from flask_login import current_user
except ImportError as e:
    logging.error(f"Failed to import app: {e}")
    sys.exit(1)

def verify_fix():
    logging.info("Starting verification...")
    
    with app.test_client() as client:
        with app.app_context():
            # Ensure tables exist
            db.create_all()
            
            # --- Test 1: Admin Login ---
            logging.info("Test 1: Admin Login")
            # Ensure admin exists
            if not Admin.query.filter_by(username='admin').first():
                logging.warning("Admin user missing, login might fail if not auto-created by route (route logic does auto-create on POST match)")
            
            # Login
            response = client.post('/admin-login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if '/admin-dashboard' in response.request.path:
                logging.info("SUCCESS: Admin redirected to /admin-dashboard")
            else:
                logging.error(f"FAILURE: Admin redirected to {response.request.path}")
                # Check for error in page
                if b"Invalid Admin Credentials" in response.data:
                    logging.error("Invalid credentials")
                
            client.get('/logout', follow_redirects=True)
            
            # --- Test 2: Donor Registration & Login ---
            logging.info("Test 2: Donor Registration")
            import time
            unique_mobile = f"99{int(time.time())}"
            
            response = client.post('/register', data={
                'full_name': 'Test Verifier',
                'mobile_number': unique_mobile,
                'password': 'password123',
                'blood_group': 'O+',
                'age': '25',
                'city': 'Test City',
                'latitude': '12.0',
                'longitude': '77.0',
                'last_donation_date': '' # None
            }, follow_redirects=True)
            
            if '/dashboard' in response.request.path and '/admin-dashboard' not in response.request.path:
                 logging.info(f"SUCCESS: Donor redirected to {response.request.path}")
            else:
                 logging.error(f"FAILURE: Donor redirected to {response.request.path}")

            # --- Test 3: Cross Access ---
            logging.info("Test 3: Cross Access (Donor accessing Admin Dashboard)")
            response = client.get('/admin-dashboard', follow_redirects=True)
            if '/dashboard' in response.request.path and '/admin-dashboard' not in response.request.path:
                logging.info("SUCCESS: Donor blocked from Admin Dashboard (Redirected to Donor Dashboard)")
            else:
                logging.error(f"FAILURE: Donor was able to access or redirected wrongly: {response.request.path}")

if __name__ == "__main__":
    verify_fix()
