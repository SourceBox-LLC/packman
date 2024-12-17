import streamlit as st
import boto3
import json
import logging
import os
from dotenv import load_dotenv
from test import load_csv, load_web, load_s3_file # Import the functions from test.py
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

# Initialize session state for delete pack
if 'show_delete_pack_selectbox' not in st.session_state:
    st.session_state.show_delete_pack_selectbox = False

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
        pack_option = st.selectbox(
            "Choose pack",
            ("", "example_pack", "example_pack2", "example_pack3"),
        )

        st.write("You selected:", pack_option)

        if st.button(f"Upload {pack_option} to Pinecone"):
            if data is not None and pack_option:
                # Format the data to be uploaded to Pinecone
                response = upload_to_pinecone(data, pack_option)
                if response:
                    st.success("Data uploaded to Pinecone successfully!")
                else:
                    st.error("Failed to upload data to Pinecone.")
            else:
                st.error("No data loaded or pack not selected. Please load data and select a pack before uploading.")
    

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
        
        # Display current packs
        packs = get_current_packs()
        if packs:
            packs_df = pd.DataFrame(packs)
            st.header("Current Packs")
            st.dataframe(packs_df, use_container_width=True)
        else:
            st.write("No packs available.")

    elif action == "Delete Pack":
        st.header("Delete a Pack")

        # Fetch current packs
        packs = get_current_packs()
        if packs:
            pack_names = [pack['Pack Name'] for pack in packs]
            selected_pack = st.selectbox("Select Pack to Delete", pack_names)

            if st.button("Confirm Delete", key="confirm_delete_button"):
                # Add logic to delete the selected pack
                st.write(f"Deleted {selected_pack}")
                # Optionally, remove the deleted pack from the packs list
                packs = [pack for pack in packs if pack['Pack Name'] != selected_pack]
                packs_df = pd.DataFrame(packs)
                st.dataframe(packs_df, use_container_width=True)
        else:
            st.write("No packs available to delete.")

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

        # Define the payload for the Lambda function
        payload = {
            "body": {
                "action": "create_pack",
                "username": "example-user",
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
else:
    login_page()


