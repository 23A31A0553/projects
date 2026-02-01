# LifeLink – Smart Blood Donation Management System

## 1. Project Abstract
**LifeLink** is a smart, web-based blood donation management system designed to bridge the gap between donors and patients in need during emergencies. Unlike traditional directories, LifeLink utilizes **Geolocation API** and a **Smart Matching Algorithm** to find the nearest, safest, and most compatible donors within seconds. The system filters donors based on health conditions, availability, and donation history to ensure patient safety. It features a responsive user dashboard, real-time blood requests, and a comprehensive admin panel for management, making blood donation efficient and accessible.

## 2. System Architecture
The system follows a typical **Model-View-Controller (MVC)** architecture:

-   **Frontend (View)**: HTML5, CSS3, JavaScript. Used for rendering responsive UI and capturing User Geolocation.
-   **Backend (Controller)**: Python (Flask). Handles routing, authentication logic (User & Admin), and the Smart Matching Algorithm.
-   **Database (Model)**: SQLite (via SQLAlchemy). Stores user profiles, health data, and request history securely.

### High-Level Data Flow:
1.  User Registers -> Data Validated -> Stored in DB (Password Hashed).
2.  Patient Requests Blood -> System captures Location -> Queries DB.
3.  **Smart Algorithm Runs**:
    -   Filters by Blood Group.
    -   Filters by Availability & Health Safety.
    -   Calculates Distance (Geopy).
    -   Sorts by Score (Distance + Recency).
4.  Results Displayed -> Patient calls Donor directly.

## 3. Database Schema

### Table: Users (Donors)
| Column | Type | Description |
| :--- | :--- | :--- |
| id | Integer (PK) | Unique ID |
| full_name | String | Donor Name |
| mobile_number | String | Unique Login ID |
| password_hash | String | Encrypted Password |
| blood_group | String | A+, B-, etc. |
| latitude/longitude | Float | Geolocation |
| health_flags | Boolean | BP, Sugar, etc. |
| last_donation_date | Date | Eligibility Check |

### Table: BloodRequests
| Column | Type | Description |
| :--- | :--- | :--- |
| id | Integer (PK) | Unique Request ID |
| patient_name | String | Patient Name |
| blood_group | String | Requested Group |
| hospital_location | String | Hospital Address |
| urgency_level | String | Low / Medium / High |

### Table: Admins
| Column | Type | Description |
| :--- | :--- | :--- |
| id | Integer | Admin ID |
| username | String | Login Username |
| password_hash | String | Secure Password |

## 4. Flow Diagram Description
1.  **Start**
2.  **Home Page** -> Login / Register
3.  **If Login**:
    -   **Donor**: Matches? -> Dashboard -> View History / Update Status / Request Blood.
    -   **Admin**: Matches? -> Admin Panel -> Manage Users.
4.  **If Request Blood**:
    -   Input Patient Details.
    -   System Locates Donors.
    -   **Algorithm Filters**: Removes < 90 days donors, Unhealthy donors.
    -   **Rank**: Nearest & Most Eligible first.
    -   Display List.
5.  **End**

## 5. Viva Explanation (Questions & Answers)

**Q: How does the Geolocation work?**
A: We use the browser's `navigator.geolocation` API in JavaScript to get the user's Latitude and Longitude. This is sent to the Flask backend, which uses the `geopy` library to calculate the distance between the requestor and donors using the Geodesic distance formula.

**Q: How is security handled?**
A: Passwords are never stored in plain text. We use `werkzeug.security.generate_password_hash` to hash passwords before storing them. Routes are protected using `Flask-Login`'s `@login_required` decorator to prevent unauthorized access.

**Q: What is the Smart Filtering logic?**
A: The system implements a scoring algorithm. It assigns a score based on Distance (closer is better), Recency (long time since last donation is safer), and Health habits (smoking/drinking reduces score). It strictly blocks anyone who donated less than 90 days ago or has critical health issues like Heart Disease.
