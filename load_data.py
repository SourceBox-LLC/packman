import logging
from langchain_community.document_loaders import WebBaseLoader
import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
    text = documents[0].page_content

    # Split the text into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Adjust chunk size as needed
        chunk_overlap=200,
    )
    texts = text_splitter.split_text(text)
    logging.info("Text split into %d chunks.", len(texts))

    return texts


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
