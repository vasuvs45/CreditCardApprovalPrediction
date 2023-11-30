# eligibility_check.py

import streamlit as st
import psycopg2
#from main_app.main_app import SessionState  # Import SessionState from main_app

# Database connection function
def connect_db():
    return psycopg2.connect(
        dbname="creditcard",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )

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

    # Fetch user details
    user_details = get_user_details(user_id)

    # Check eligibility based on user_details and credit_card_details tables
    cursor.execute("""
        SELECT * FROM user_details u
        JOIN credit_card_details c ON u.minimum_credit_score >= c.minimum_credit_score
                                  AND u.minimum_credit_limit >= c.minimum_past_credit_limit
                                  AND u.minimum_credit_history >= c.minimum_credit_history
                                  AND u.minimum_income_requirement >= c.minimum_income_requirement
        WHERE u.user_id = %s
    """, (user_id,))

    eligible_cards = cursor.fetchall()

    conn.close()

    return eligible_cards

# Eligibility Check Page
def eligibility_check_page(session_state):
    st.title("Credit Card Eligibility Check")

    # Get user details from session state
    email_id = session_state.email_id

    # Fetch user details
    user_data = get_user_details(email_id)

    if user_data:
        st.success(f"Welcome, {user_data[1]} {user_data[2]}!")

        # Get user details from the user
        credit_score = st.number_input("Enter your minimum credit score:", min_value=0, max_value=1000, step=1)
        credit_limit = st.number_input("Enter your minimum credit limit:", min_value=0, max_value=1000000, step=100)
        credit_history = st.number_input("Enter your minimum credit history (in months):", min_value=0, max_value=100, step=1)
        income_requirement = st.number_input("Enter your minimum income requirement:", min_value=0, max_value=10000000, step=1000)

        # Button to check eligibility
        if st.button("Check Eligibility"):
            # Check eligibility
            eligible_cards = check_eligibility(user_data[0], credit_score, credit_limit, credit_history, income_requirement)

            if eligible_cards:
                st.success("Congratulations! You are eligible for the following credit cards:")
                for card in eligible_cards:
                    st.write(card[5])  # Assuming credit_card column is at index 5, adjust accordingly
            else:
                st.warning("Sorry, you are not eligible for any credit cards.")
    else:
        st.error("User not found. Please log in with a valid email.")

from main_app import SessionState