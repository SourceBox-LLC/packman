import streamlit as st
import boto3
import json
import logging
import os
from dotenv import load_dotenv
from test import load_csv, load_web, load_s3_file  # Import the functions from test.py
import pandas as pd

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

# Function to fetch current packs
def get_current_packs():
    # Placeholder data; replace with actual data retrieval logic
    packs = [
        {'Pack Name': 'Starter Pack', 'Description': 'This is the starter pack.', 'Date Created': '2023-01-01'},
        {'Pack Name': 'Advanced Pack', 'Description': 'This pack contains advanced features.', 'Date Created': '2023-02-15'},
        {'Pack Name': 'Pro Pack', 'Description': 'For professionals and businesses.', 'Date Created': '2023-03-10'},
    ]
    return packs

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

    st.title("Main Page")
    st.write("Welcome to the main page!")
    st.write(f"Access Token: {st.session_state.access_token}")
    
    # Add an action selectbox at the top
    action = st.selectbox(
        "Choose an action",
        ("Update Pack", "Create Pack", "Delete Pack"),
    )

    if action == "Update Pack":
        # Existing logic continues here
        # Select data type
        st.subheader("Data Uploads")
        option = st.selectbox(
            "Choose data type",
            ("Webpage", "LocalFile", "AWS S3"),
        )

        st.write("You selected:", option)

        if option == "Webpage":
            url = st.text_input("Webpage URL", "https://en.wikipedia.org/wiki/Elon_Musk")
            if url:
                # Load the web page content
                data = load_web(url)
                st.write("Loaded web page content:")
                st.write(data[:1000])  # Display the first 1000 characters

        elif option == "LocalFile":
            uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt"])
            if uploaded_file is not None:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load the document using load_csv
                data = load_csv([temp_file_path])
                st.write("Loaded document content:")
                st.write(data[:1000])  # Display the first 1000 characters
                
                # Clean up the temporary file if needed
                os.remove(temp_file_path)

        elif option == "AWS S3":
            bucket = st.text_input("Bucket Name", "public-test543464")
            file_name = st.text_input("File Name", "customers-full.csv")
            if bucket and file_name:
                # Load the full file content from S3
                docs = load_s3_file(bucket, file_name)
                st.write("Loaded S3 file content:")
                st.write(docs[:1000])  # Display the first 1000 characters of the content
        
        else:
            st.write("Please select a data type")
        
        # choose pack to uplaod data
        st.subheader("Choose pack to upload data")
        option = st.selectbox(
            "Choose data type",
            ("", "example_pack", "example_pack2", "example_pack3"),
        )

        st.write("You selected:", option)
    

    if action == "Create Pack":
        st.header("Create a New Pack")
        
        # Create a form for creating a new pack
        with st.form(key='create_pack_form'):
            pack_name = st.text_input("Pack Name")
            pack_description = st.text_area("Pack Description")
            submit_button = st.form_submit_button(label='Submit')
        
        if submit_button:
            if pack_name and pack_description:
                st.write(f"**Pack Name:** {pack_name}")
                st.write(f"**Pack Description:** {pack_description}")
                # You can add more logic here to process the pack creation
                st.success("Pack created successfully!")
            else:
                st.error("Please enter both the pack name and description.")
        
        #display current packs
        display_packs_with_delete()

    elif action == "Update Pack":
        st.write("Update Pack functionality is under development.")

    elif action == "Delete Pack":
        st.write("Delete Pack functionality is under development.")

    else:
        st.write("Please select an action to proceed.")

def display_packs_with_delete():
    packs = get_current_packs()
    if packs:
        st.subheader("Current Packs")
        for pack in packs:
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            with col1:
                st.write(pack['Pack Name'])
            with col2:
                st.write(pack['Description'])
            with col3:
                st.write(pack['Date Created'])
            with col4:
                if st.button(f"Delete {pack['Pack Name']}", key=f"delete_{pack['Pack Name']}"):
                    # Add logic to delete the pack
                    st.write(f"Deleted {pack['Pack Name']}")
    else:
        st.write("No packs available.")

# Display the appropriate page based on login state
if st.session_state.logged_in:
    main_page()
else:
    login_page()


