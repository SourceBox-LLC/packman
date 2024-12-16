from langchain_community.document_loaders import UnstructuredCSVLoader
from langchain_community.document_loaders import WebBaseLoader
import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError


#load csv
def load_csv(file_paths):
    loader = UnstructuredCSVLoader(file_paths[0])
    return loader.load()


#load web
def load_web(url):
    loader_web = WebBaseLoader(
        url
    )
    return loader_web.load()


# Load S3 file
def load_s3_file(bucket_name, file_name):
    s3 = boto3.client('s3')
    temp_file_path = f"temp_{file_name}"
    try:
        # Download the file from S3 to a temporary location
        s3.download_file(bucket_name, file_name, temp_file_path)
        
        # Read the file
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        
        return data
    except NoCredentialsError:
        return "AWS credentials not found."
    except ClientError as e:
        return f"Error downloading file: {e}"
    finally:
        # Remove the temporary file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)