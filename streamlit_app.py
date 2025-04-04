import streamlit as st
import boto3
import json
import logging
import os
import requests
from dotenv import load_dotenv
from load_data import load_csv, load_web, load_s3_file
import pandas as pd

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API URL
API_URL = os.getenv('API_URL', 'http://localhost:5000')

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'logout_trigger' not in st.session_state:
    st.session_state.logout_trigger = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'register_trigger' not in st.session_state:
    st.session_state.register_trigger = False

# Initialize session state for delete pack
if 'show_delete_pack_selectbox' not in st.session_state:
    st.session_state.show_delete_pack_selectbox = False

# Initialize a session using Boto3 for S3 operations only
session = boto3.Session(
    aws_access_key_id=st.secrets["default"]["ACCESS_KEY"],
    aws_secret_access_key=st.secrets["default"]["SECRET_KEY"],
    region_name=st.secrets["default"]["REGION"]
)

# Create a Lambda client for non-auth operations
lambda_client = session.client('lambda')

# Function to toggle registration page
def register_trigger():
    st.session_state.register_trigger = True

# Function to go back to login page
def back_to_login():
    st.session_state.register_trigger = False

# Function to fetch current packs
def get_current_packs():
    try:
        # Make a request to the Flask API to get user packs
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(f'{API_URL}/user/packs', headers=headers)
        
        if response.status_code == 200:
            packs = response.json()
            
            # Transform the data to match the expected format
            formatted_packs = []
            for pack in packs:
                formatted_packs.append({
                    'Pack Name': pack['pack_name'],
                    'Description': pack['description'],
                    'Date Created': pack['date_created'].split('T')[0] if 'T' in pack['date_created'] else pack['date_created'],
                    'Pack ID': pack['id']
                })
            return formatted_packs
        else:
            logging.error("Failed to fetch packs: %s", response.text)
            return []
            
    except Exception as e:
        logging.error("Error fetching packs: %s", e)
        return []

# Function to display the login page
def login_page():
    st.title("Login Page")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    # Create a button to navigate to the registration page
    st.button("Don't have an account? Register here", on_click=register_trigger)

    if submit_button:
        logging.info("Login attempt for user: %s", username)
        
        try:
            # Make a request to the Flask API for login
            response = requests.post(
                f'{API_URL}/login',
                json={
                    'username': username,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.logged_in = True
                st.session_state.access_token = data['access_token']
                st.session_state.username = username
                st.session_state.user_id = data['user_id']
                logging.info("User %s logged in successfully.", username)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                logging.warning("Invalid login attempt for user: %s", username)
                st.error("Invalid username or password")
                
        except Exception as e:
            logging.error("Error during login: %s", e)
            st.error("An error occurred while processing your request.")

# Function to log out the user
def logout():
    logging.info("User logged out.")
    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.logout_trigger = not st.session_state.logout_trigger

# Function to display the main page
def main_page():
    st.sidebar.title("Navigation")
    st.sidebar.button("Logout", on_click=logout)

    st.title("Main Page")
    st.write("Welcome to the main page!")
    
    # Add an action selectbox at the top
    action = st.selectbox(
        "Choose an action",
        ("Create Pack", "Delete Pack"),
    )

    if action == "Create Pack":
        st.header("Create a New Pack")
        
        # Create a form for creating a new pack
        with st.form(key='create_pack_form'):
            pack_name = st.text_input("Pack Name")
            pack_description = st.text_area("Pack Description")
            submit_button = st.form_submit_button(label='Submit')
        
        if submit_button:
            if pack_name and pack_description:
                try:
                    # Make a request to the Flask API to create a new pack
                    headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
                    response = requests.post(
                        f'{API_URL}/user/packs',
                        headers=headers,
                        json={
                            'pack_name': pack_name,
                            'description': pack_description
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        st.success("Pack created successfully!")
                        logging.info("Pack created successfully: %s", response.text)
                        st.rerun()
                    else:
                        st.error("Failed to create pack. Please try again.")
                        logging.error("Failed to create pack: %s", response.text)
                    
                except Exception as e:
                    st.error("An error occurred while creating the pack.")
                    logging.error("Error creating pack: %s", e)
            else:
                st.error("Please enter both the pack name and description.")
        
        # Display current packs
        packs = get_current_packs()
        if packs:
            packs_df = pd.DataFrame(packs)
            st.header("Current Packs")
            st.dataframe(packs_df, use_container_width=True)
        else:
            st.write("No packs available.")

        # Initialize data
        data = None

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
                # Load and split the web page content
                data = load_web(url)
                st.write("Loaded web page content splits:")
                st.write(data[:5])  # Display the first 5 chunks

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
                st.write(data.head())  # Display the first few rows

                # Clean up the temporary file
                os.remove(temp_file_path)

        elif option == "AWS S3":
            bucket = st.text_input("Bucket Name", "public-test543464")
            file_name = st.text_input("File Name", "customers-full.csv")
            if bucket and file_name:
                # Load the full file content from S3
                data = load_s3_file(bucket, file_name)
                if data is not None:
                    st.write("Loaded S3 file content:")
                    st.write(data.head())  # Display the first few rows
                else:
                    st.error("Failed to load data from S3.")

        else:
            st.write("Please select a data type")

        # Choose pack to upload data
        st.subheader("Choose pack to upload data")
        pack_names = [pack['Pack Name'] for pack in packs]  # Get pack names from current packs
        pack_option = st.selectbox(
            "Choose pack",
            [""] + pack_names,  # Add an empty option for default
        )

        st.write("You selected:", pack_option)

        # Initialize session state for storing selected packs and data
        if 'selected_packs' not in st.session_state:
            st.session_state.selected_packs = []
        if 'uploaded_data' not in st.session_state:
            st.session_state.uploaded_data = []

        # Add another pack
        if st.button("Add data to pack"):
            if pack_option and data is not None:
                st.session_state.selected_packs.append(pack_option)
                st.session_state.uploaded_data.append(data)
                st.write(f"Added {pack_option} with data to session.")
                # Reset the selection and data
                st.session_state.show_delete_pack_selectbox = False
                st.rerun()

        # Upload all data to Pinecone
        if st.button("Upload all data to Pinecone"):
            if st.session_state.uploaded_data and st.session_state.selected_packs:
                for pack, data in zip(st.session_state.selected_packs, st.session_state.uploaded_data):
                    response = upload_to_pinecone(data, pack)
                    if response:
                        st.success(f"Data for {pack} uploaded to Pinecone successfully!")
                    else:
                        st.error(f"Failed to upload data for {pack} to Pinecone.")
                # Clear session data after upload
                st.session_state.selected_packs.clear()
                st.session_state.uploaded_data.clear()
            else:
                st.error("No data loaded or pack not selected. Please load data and select a pack before uploading.")

    elif action == "Delete Pack":
        st.header("Delete a Pack")

        # Fetch current packs
        packs = get_current_packs()
        if packs:
            # Create a dictionary to map pack names to their IDs
            pack_name_to_id = {pack['Pack Name']: pack['Pack ID'] for pack in packs}
            pack_names = list(pack_name_to_id.keys())
            
            selected_pack = st.selectbox("Select Pack to Delete", pack_names)

            if st.button("Confirm Delete", key="confirm_delete_button"):
                try:
                    # Delete pack using Flask API
                    headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
                    pack_id = pack_name_to_id[selected_pack]
                    response = requests.delete(f'{API_URL}/user/packs/{pack_id}', headers=headers)
                    
                    if response.status_code in [200, 204]:
                        # Now handle Pinecone deletion via Lambda (this part remains the same)
                        pinecone_payload = {
                            "body": {
                                "action": "delete_pack",
                                "username": st.session_state.username,
                                "pack_name": selected_pack
                            }
                        }

                        pinecone_response = lambda_client.invoke(
                            FunctionName='pinecone-embedding-HelloWorldFunction-tHPspSqIP5SE',
                            InvocationType='RequestResponse',
                            Payload=json.dumps(pinecone_payload)
                        )
                        
                        pinecone_response_payload = json.loads(pinecone_response['Payload'].read())

                        # Handle Pinecone response
                        if 'errorMessage' in pinecone_response_payload:
                            if "does not exist" in pinecone_response_payload['errorMessage']:
                                st.success(f"Pack {selected_pack} deleted successfully. It was already removed from Pinecone.")
                            else:
                                st.warning(f"Pack {selected_pack} deleted from database, but had an issue with Pinecone: {pinecone_response_payload['errorMessage']}")
                        else:
                            st.success(f"Successfully deleted pack: {selected_pack}")
                        
                        logging.info(f"Pack deleted from database: {response.text}, Pinecone: {pinecone_response_payload}")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete pack. Server responded with: {response.status_code}")
                        logging.error(f"Delete failed - API response: {response.text}")

                except Exception as e:
                    st.error("An error occurred while deleting the pack.")
                    logging.error("Error deleting pack: %s", e)

        else:
            st.write("No packs available to delete.")

    else:
        st.write("Please select an action to proceed.")

def register_page():
    st.title("Register Page")
    
    # Add a button to go back to login
    st.button("Back to Login", on_click=back_to_login)
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")

        if submit_button:
            if not username or not email or not password:
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    # Make a request to the Flask API to register a new user
                    response = requests.post(
                        f'{API_URL}/register',
                        json={
                            'username': username,
                            'email': email,
                            'password': password
                        }
                    )
                    
                    if response.status_code == 201:
                        st.success("Registration successful! You can now log in.")
                        # Go back to login page after successful registration
                        st.session_state.register_trigger = False
                        st.rerun()
                    elif response.status_code == 409:
                        data = response.json()
                        st.error(f"Registration failed: {data.get('message', 'Username or email already exists')}")
                    else:
                        st.error(f"Registration failed: {response.status_code}")
                        
                except Exception as e:
                    logging.error("Error during registration: %s", e)
                    st.error("An error occurred during registration. Please try again later.")



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

def format_data_for_pinecone(data):
    formatted_data = []

    # Check if data is a list of strings
    if isinstance(data, list) and all(isinstance(item, str) for item in data):
        for i, text in enumerate(data):
            formatted_data.append({"id": f"vec{i+1}", "text": text})

    # Check if data is a DataFrame
    elif isinstance(data, pd.DataFrame):
        # Replace 'your_text_column_name' with the actual column name containing text
        text_column = 'your_text_column_name'
        if text_column in data.columns:
            for i, row in data.iterrows():
                text = str(row[text_column])
                formatted_data.append({"id": f"vec{i+1}", "text": text})
        else:
            # If the text column is not found, concatenate all columns
            for i, row in data.iterrows():
                text = ' '.join(str(value) for value in row.values)
                formatted_data.append({"id": f"vec{i+1}", "text": text})
    else:
        logging.error("Unsupported data type for formatting.")

    logging.info("Checking chunk sizes:")
    for i, entry in enumerate(formatted_data):
        text_size = len(entry['text'].encode('utf-8'))
        logging.info("Chunk %d size: %d bytes", i+1, text_size)

    return formatted_data

def upload_to_pinecone(data, index_name):
    logging.info("Uploading data to Pinecone with index name: %s", index_name)
    logging.info("Data type before formatting: %s", type(data))
    if isinstance(data, pd.DataFrame):
        logging.info("Data content before formatting:\n%s", data.head())
    else:
        logging.info("Data content before formatting:\n%s", data)

    # Format the data
    formatted_data = format_data_for_pinecone(data)
    logging.info("Formatted data: %s", formatted_data)

    # Batch the data
    batch_size = 96  # Maximum inputs per batch for the model
    batches = [formatted_data[i:i + batch_size] for i in range(0, len(formatted_data), batch_size)]
    logging.info("Total batches to upload: %d", len(batches))

    # Initialize a session using Boto3
    session = boto3.Session(
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('SECRET_KEY'),
        region_name=os.getenv('REGION')
    )

    # Create a Lambda client
    lambda_client = session.client('lambda')

    # Iterate over each batch and send to Lambda
    for batch_number, batch_data in enumerate(batches, start=1):
        logging.info("Uploading batch %d with %d records", batch_number, len(batch_data))

        # Define the payload for the Lambda function with actual username
        payload = {
            "body": {
                "action": "create_pack",
                "username": st.session_state.username,  # Using actual username from session state
                "data": batch_data,
                "pack_name": index_name
            }
        }

        # Invoke the Lambda function
        try:
            response = lambda_client.invoke(
                FunctionName='pinecone-embedding-HelloWorldFunction-tHPspSqIP5SE',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            logging.info("Lambda function invoked successfully for batch %d.", batch_number)

            # Read the response
            response_payload = json.loads(response['Payload'].read())
            logging.info("Received response from Lambda for batch %d: %s", batch_number, response_payload)

            # Check for errors in the response
            if 'errorMessage' in response_payload:
                logging.error("Error in Lambda invocation for batch %d: %s", batch_number, response_payload['errorMessage'])
                return None

        except Exception as e:
            logging.error("Error invoking Lambda function for batch %d: %s", batch_number, e)
            return None

    return True  # Return True if all batches uploaded successfully

# Display the appropriate page based on login state
if st.session_state.logged_in:
    main_page()
elif st.session_state.register_trigger:
    register_page()
else:
    login_page()


