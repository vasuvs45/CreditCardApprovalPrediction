# main_app.py

import streamlit as st
import psycopg2
from passlib.hash import pbkdf2_sha256
import pandas as pd
# Database Connection

def connect_db():
    return psycopg2.connect(
        dbname="creditcard",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )

# Create tables

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


# Define SessionState class
class SessionState:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


# Function to initialize session state
def init_session_state():
    if not hasattr(st.session_state, 'logged_in'):
        st.session_state.logged_in = False
        st.session_state.email_id = None
        st.session_state.updated_credit_score = None
        st.session_state.updated_credit_limit = None
        st.session_state.updated_credit_history = None
        st.session_state.updated_income_requirement = None
        st.session_state.user_id = None  # Add this line to initialize user_id


# SignUp Page

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

# Function to create a new user

def create_user(first_name, last_name, email_id, new_password, address, phone_number):
    # Function to create a new user
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if the username already exists
        cursor.execute(
            "SELECT * FROM profile WHERE email_id = %s", (email_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            return False

        # Insert new user into the profile table
        hashed_password = hash_password(new_password)
        cursor.execute("INSERT INTO profile (first_name, last_name, email_id, password, phone_number, address) VALUES (%s, %s, %s, %s, %s, %s)",
                       (first_name, last_name, email_id, hashed_password, phone_number, address))

        conn.commit()
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


# Login
def login():
    st.subheader("Login")

    # Input fields
    email_id = st.text_input("Email Id")
    password = st.text_input("Password", type="password")

    # Check if the user has clicked the "Login" button
    if st.button("Login"):
        # Verify credentials
        if verify_credentials(email_id, password):
            st.session_state.logged_in = True
            st.session_state.email_id = email_id
            st.success("Logged in as {}".format(email_id))
        else:
            st.error("Invalid credentials")


def verify_credentials(email_id, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email_id, password FROM profile WHERE email_id = %s", (email_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and verify_password(password, user_data[1]):
        return True
    else:
        return False


# Function to display credit details form
def credit_details(email_id):
    st.header("Insert your credit details below")
    # Add credit details form elements here
    min_credit_score = st.slider(
        "Minimum Credit Score", min_value=300, max_value=850, value=500)
    min_credit_limit = st.number_input("Minimum Credit Limit", value=1000)
    min_credit_history = st.number_input(
        "Minimum Credit History (in months)", value=12)
    min_income_requirement = st.number_input(
        "Minimum Income Requirement", value=30000)

    if st.button("INSERT DETAILS AND CHECK ELIGIBILITY"):
        user_data = get_user_details(email_id)
        user_id = user_data[0]
        create_profile_flag = create_credit_profile(
            user_id, min_credit_score, min_credit_limit, min_credit_history, min_income_requirement)
        if create_profile_flag:
            eligible_cards = check_eligibility(
                user_id, min_credit_score, min_credit_limit, min_credit_history, min_income_requirement)
        else:
            st.warning("You have already inserted your information once. Please Update your information from side bar")
            return
        if eligible_cards:
            # Dropdown
            selected_card = st.selectbox(
                "Avaliable Credit Card", eligible_cards)
            st.write(f"Selected Credit Card: {selected_card}")
        else:
            st.warning("No eligible credit cards found.")

    # if st.button("Delete my credit information"):
    #     user_data = get_user_details(email_id)
    #     user_id = user_data[0]
    #     delete_flag = delete_credit_information(user_id)
    #     if delete_flag:
    #         st.success(
    #             "Deleted credit information for user with mail  {}".format(email_id))
    #     else:
    #         st.error("Invalid credentials")

def create_credit_profile(user_id, credit_score, credit_limit, credit_history, income_requirement):
    conn = connect_db()
    cursor = conn.cursor()
    # Check if the username already exists
    cursor.execute(
        "SELECT * FROM user_details WHERE user_id = %s", (user_id,))
    existing_user = cursor.fetchone()
    if existing_user:
        return False
    cursor.execute("INSERT INTO user_details (user_id, minimum_credit_score, minimum_credit_limit, minimum_credit_history, minimum_income_requirement) VALUES (%s, %s, %s, %s, %s)",
                   (user_id, credit_score, credit_limit, credit_history, income_requirement))
    conn.commit()
    conn.close()
    return True

# Function to fetch user details based on email_id

def get_user_details(email_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE email_id = %s", (email_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data


# Function to check credit card eligibility
def check_eligibility(user_id, credit_score, credit_limit, credit_history, income_requirement):
    conn = connect_db()
    cursor = conn.cursor()

    # Check eligibility based on user_details and credit_card_details tables
    cursor.execute("""
        SELECT credit_card FROM user_details u
        JOIN credit_card_details c ON u.minimum_credit_score >= c.minimum_credit_score
                                  AND u.minimum_credit_limit >= c.minimum_past_credit_limit
                                  AND u.minimum_credit_history >= c.minimum_credit_history
                                  AND u.minimum_income_requirement >= c.minimum_income_requriement
        WHERE u.user_id = %s
    """, (user_id,))

    eligible_cards = cursor.fetchall()

    conn.close()

    return eligible_cards

# Update Credit Information


def update_credit_information(email_id):
    st.header("Update your credit details here")
    # Input fields for updating credit information
    updated_credit_score = st.slider(
        "Updated Minimum Credit Score", min_value=300, max_value=850, value=500)
    updated_credit_limit = st.number_input(
        "Updated Minimum Credit Limit", value=1000)
    updated_credit_history = st.number_input(
        "Updated Minimum Credit History (in months)", value=12)
    updated_income_requirement = st.number_input(
        "Updated Minimum Income Requirement", value=30000)
    

    # Check if the user has clicked the "Update" button
    if st.button("UPDATE DETAILS AND CHECK ELIGIBILITY"):
        user_data = get_user_details(email_id)
        user_id = user_data[0]
        print("Update for user_id:",user_id)
        # Call the function to update credit information
        update_flag = update_user_credit_information(
            user_id, updated_credit_score, updated_credit_limit, updated_credit_history, updated_income_requirement)
        if update_flag:
            new_eligible_cards = check_eligibility(user_id, updated_credit_score, updated_credit_limit, updated_credit_history, updated_income_requirement)
            st.success("Credit information updated successfully")
        else:
            st.error("Credit Details for this user are unavailable.Please select Credit Detials Option from Side Bar.")
            return
        if new_eligible_cards:
            # Dropdown
            selected_card = st.selectbox(
                "Avaliable Credit Card", new_eligible_cards)
            st.write(f"Selected Credit Card: {selected_card}")
        else:
            st.warning("Still not eligible for any of the credit cards.")

# Function to update user's credit information

def update_user_credit_information(user_id, updated_credit_score, updated_credit_limit, updated_credit_history, updated_income_requirement):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Update user_details table with the new credit information
        print(user_id, updated_credit_score, updated_credit_limit, updated_credit_history, updated_income_requirement)
        
        #Check if user present or not
        cursor.execute(
        "SELECT * FROM user_details WHERE user_id = %s", (user_id,))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.execute("""
                UPDATE user_details
                SET minimum_credit_score = %s,
                    minimum_credit_limit = %s,
                    minimum_credit_history = %s,
                    minimum_income_requirement = %s
                WHERE user_id = %s
            """, (updated_credit_score, updated_credit_limit, updated_credit_history, updated_income_requirement, user_id))
            conn.commit()
            conn.close()
            return True
        return False

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def delete_credit_information(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    #delete_flag = 0
    # Check if the username already exists
    cursor.execute(
        "SELECT * FROM user_details WHERE user_id = %s", (user_id,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.execute("DELETE FROM user_details where user_id = %s",
                   (user_id,))
        conn.commit()
        conn.close()
        return True
    return False

def delete_information(email_id):
    st.header("Do you really want to delete crdit information")
    # Input fields for updating credit information
    # Check if the user has clicked the "Update" button
    if st.button("DELETE CREDIT DETAILS"):
        user_data = get_user_details(email_id)
        user_id = user_data[0]
        print("Delete for user_id:",user_id)
        # Call the function to update credit information
        deleted_flag = delete_credit_information(user_id)
        if deleted_flag:
            st.success(
                "Deleted credit information for user with mail  {} sucessfully".format(email_id))
        else:
            st.error("Your Credit information is unavailalbe with us.")

# Logout function
def logout():
    # Reset session state on logout
    st.session_state.logged_in = False
    st.session_state.email_id = None
    st.session_state.updated_credit_score = None
    st.session_state.updated_credit_limit = None
    st.session_state.updated_credit_history = None
    st.session_state.updated_income_requirement = None
    st.session_state.user_id = None
    st.sidebar.success("Logged out successfully")


def main():
    # Initialize session state
    init_session_state()

    st.title("Credit Card Eligibility Checker")

    # Sidebar with login, signup, and logout options
    menu = []

    if not st.session_state.logged_in:
        menu.append("Login")
        menu.append("Signup")
    else:
        menu.append("Credit Details")
        menu.append("Update Details")  # Add "Update Details" option
        menu.append("Delete Details")
        menu.append("Logout")

    choice = st.sidebar.selectbox("Select Option", menu)

    if choice == "Signup":
        signup()
    elif choice == "Login":
        login()
    elif choice == "Logout":
        logout()
    elif choice == "Credit Details":
        credit_details(st.session_state.email_id)
    elif choice == "Update Details":
        update_credit_information(st.session_state.email_id)
    elif choice == "Delete Details":
        delete_information(st.session_state.email_id)

if __name__ == "__main__":
    main()
