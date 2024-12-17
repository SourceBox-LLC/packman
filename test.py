import logging
from langchain_community.document_loaders import UnstructuredCSVLoader, WebBaseLoader
import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
import pandas as pd
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load CSV
def load_csv(file_paths):
    logging.info("Loading CSV from file path: %s", file_paths[0])
    data = pd.read_csv(file_paths[0])
    logging.info("CSV loaded into DataFrame successfully.")
    return data

# Load web
def load_web(url):
    logging.info("Loading web content from URL: %s", url)
    loader_web = WebBaseLoader(url)
    documents = loader_web.load()
    logging.info("Web content loaded successfully.")

    # Extract text from the loaded documents
    data = [doc.page_content for doc in documents]
    return data

# Load S3 file
def load_s3_file(bucket_name, file_name):
    logging.info("Loading file from S3 bucket: %s, file: %s", bucket_name, file_name)
    s3 = boto3.client('s3')
    temp_file_path = f"temp_{file_name}"
    try:
        # Download the file from S3 to a temporary location
        s3.download_file(bucket_name, file_name, temp_file_path)
        logging.info("File downloaded successfully from S3.")

        # Read the file into a DataFrame
        data = pd.read_csv(temp_file_path)
        logging.info("File read into DataFrame successfully.")
        return data
    except NoCredentialsError:
        logging.error("AWS credentials not found.")
        return None
    except ClientError as e:
        logging.error("Error downloading file: %s", e)
        return None
    except Exception as e:
        logging.error("Error reading file into DataFrame: %s", e)
        return None
    finally:
        # Remove the temporary file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Temporary file removed.")

# Upload to Pinecone
def upload_to_pinecone(data, index_name):
    logging.info("Uploading data to Pinecone with index name: %s", index_name)
    # Format the data
    formatted_data = format_data_for_pinecone(data)
    
    # Initialize a session using Boto3
    session = boto3.Session(
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('SECRET_KEY'),
        region_name=os.getenv('REGION')
    )

    # Create a Lambda client
    lambda_client = session.client('lambda')

    # Define the payload for the Lambda function
    payload = {
        "body": {
            "action": "create_pack",
            "username": "example-user",
            "data": formatted_data,
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
        logging.info("Lambda function invoked successfully.")
        
        # Read the response
        response_payload = json.loads(response['Payload'].read())
        logging.info("Received response from Lambda: %s", response_payload)
        
        return response_payload
    except Exception as e:
        logging.error("Error invoking Lambda function: %s", e)
        return None