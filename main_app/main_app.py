# main_app.py

import streamlit as st
import psycopg2
from passlib.hash import pbkdf2_sha256
#from eligibility_check import eligibility_check_page  # Import the eligibility_check_page
from eligibility_check.eligibility_check import eligibility_check_page
#from utils import connect_db, hash_password, verify_password, create_user,eligibility_check_page

# Define SessionState class
class SessionState:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

# Database connection function
def connect_db():
    return psycopg2.connect(
        dbname="creditcard",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )

# Function to create tables if they don't exist
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile 
        (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email_id VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(100),
            phone_number BIGINT NOT NULL,
            address VARCHAR(100)
        );
        CREATE TABLE IF NOT EXISTS user_details
        (
            user_id INT REFERENCES profile(id),
            minimum_credit_score INT,
            minimum_credit_limit INT,
            minimum_credit_history INT,
            minimum_income_requirement INT
        );
    ''')
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return pbkdf2_sha256.hash(password)

# Function to verify passwords
def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)

# Streamlit app
def main():
    st.title("Login and Signup App")

    # Create tables if they don't exist
    create_tables()

    # Sidebar with login and signup options
    menu = ["Login", "Signup"]
    choice = st.sidebar.selectbox("Select Option", menu)

    if choice == "Login":
        login()
    elif choice == "Signup":
        signup()

# Login page
def login():
    st.subheader("Login")

    # Input fields
    email_id = st.text_input("Email Id")
    password = st.text_input("Password", type="password")

    # Check if the user has clicked the "Login" button
    if st.button("Login"):
        # Verify credentials
        if verify_credentials(email_id, password):
            # Set session state variables
            session_state = SessionState(logged_in=True, email_id=email_id)
            st.success("Logged in as {}".format(email_id))
            
            # Redirect to the eligibility check page
            eligibility_check_page(session_state)
        else:
            st.error("Invalid credentials")

# Signup page
def signup():
    st.subheader("Signup")

    # Input fields
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    new_password = st.text_input("Password", type="password")    
    email_id = st.text_input("Email ID")
    address = st.text_input("Address")
    phone_number = st.number_input("Phone Number", step=1)

    # Check if the user has clicked the "Signup" button
    if st.button("Signup"):
        # Hash password and store in the database
        if create_user(first_name, last_name, email_id, new_password, address, phone_number):
            st.success("Account created for {}".format(email_id))
        else:
            st.error("Email Id already exists")

# Function to verify login credentials
def verify_credentials(email_id, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email_id, password FROM profile WHERE email_id = %s", (email_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and verify_password(password, user_data[1]):
        return True
    else:
        return False

# Function to create a new user
def create_user(first_name, last_name, email_id, new_password, address, phone_number):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM profile WHERE email_id = %s", (email_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return False
    else:
        # Insert new user into the database
        hashed_password = hash_password(new_password)
        cursor.execute("INSERT INTO profile (first_name, last_name, email_id, password, phone_number, address) VALUES (%s, %s, %s, %s, %s, %s)", (first_name, last_name, email_id, hashed_password, phone_number, address))
        conn.commit()
        conn.close()
        return True

if __name__ == "__main__":
    main()
