import streamlit as st
import boto3
import json
import logging
import os
from dotenv import load_dotenv
from test import load_csv, load_web, load_s3_file  # Import the functions from test.py

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'logout_trigger' not in st.session_state:
    st.session_state.logout_trigger = False

# Initialize a session using Boto3
session = boto3.Session(
    aws_access_key_id=os.getenv('ACCESS_KEY'),
    aws_secret_access_key=os.getenv('SECRET_KEY'),
    region_name=os.getenv('REGION')
)

# Create a Lambda client
lambda_client = session.client('lambda')

# Function to display the login page
def login_page():
    st.title("Login Page")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        logging.info("Login attempt for user: %s", username)
        
        # Define the payload for the Lambda function
        payload = {
            "action": "LOGIN_USER",
            "data": {
                "username": username,
                "password": password
            }
        }

        # Invoke the Lambda function
        try:
            response = lambda_client.invoke(
                FunctionName='sb-user-auth-sbUserAuthFunction-3StRr85VyfEC',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            logging.info("Lambda function invoked successfully.")
        except Exception as e:
            logging.error("Error invoking Lambda function: %s", e)
            st.error("An error occurred while processing your request.")
            return

        # Read the response
        response_payload = json.loads(response['Payload'].read())
        logging.info("Received response from Lambda: %s", response_payload)

        # Check the response and update session state
        if response_payload.get('statusCode') == 200:
            st.session_state.logged_in = True
            st.session_state.access_token = json.loads(response_payload['body'])['token']
            logging.info("User %s logged in successfully.", username)
            st.success("Logged in successfully!")
            st.rerun()
        else:
            logging.warning("Invalid login attempt for user: %s", username)
            st.error("Invalid username or password")

# Function to log out the user
def logout():
    logging.info("User logged out.")
    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.logout_trigger = not st.session_state.logout_trigger  # Toggle the trigger

# Function to display the main page
def main_page():
    st.sidebar.title("Navigation")
    st.sidebar.button("Logout", on_click=logout)
    #st.sidebar.button("Create Pack", on_click=create_pack)
    #st.sidebar.button("Update Pack", on_click=update_pack)
    #st.sidebar.button("Delete Pack", on_click=delete_pack)

    st.title("Main Page")
    st.write("Welcome to the main page!")
    st.write(f"Access Token: {st.session_state.access_token}")

    # Select Action type
    option = st.selectbox(
        "Choose action type",
        ("Create Pack", "Update Pack", "Delete Pack"),
    )

    st.write("You selected:", option)
    
    # Select data type
    option = st.selectbox(
        "Choose data type",
        ("Webpage", "LocalFile", "AWS S3"),
    )

    st.write("You selected:", option)

    if option == "Webpage":
        url = st.text_input("Webpage URL", "https://en.wikipedia.org/wiki/Elon_Musk")
        if url:
            # Load the web page using WebBaseLoader
            docs = load_web(url)
            st.subheader("Loaded web page preview:")
            for doc in docs:
                st.write(doc.page_content[:1000])  # Display first 1000 characters of the document
    
    elif option == "LocalFile":
        uploaded_file = st.file_uploader("Upload a file", type=["csv"])
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load the document using UnstructuredCSVLoader
            docs = load_csv([temp_file_path])
            st.subheader("Loaded document preview:")
            for doc in docs:
                st.write(doc.page_content[:1000])  # Display first 1000 characters of the document
            
            # Clean up the temporary file if needed

    elif option == "AWS S3":
        bucket = st.text_input("Bucket Name", "public-test543464")
        file_name = st.text_input("File Name", "customers-full.csv")
        if bucket and file_name:
            # Load the file from S3 using S3DirectoryLoader
            docs = load_s3_file(bucket, file_name)
            st.subheader("Loaded S3 file preview:")
            st.write(docs[:1000])  # Display the first 1000 characters of the content
    
    else:
        st.write("Please select a data type")
    
    # Submit button
    data = None
    if st.button("Add Data"):
        st.write(f"Data submitted successfully: {data}")

# Display the appropriate page based on login state
if st.session_state.logged_in:
    main_page()
else:
    login_page()


