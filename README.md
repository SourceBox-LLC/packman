# PackMan Application

This application provides functionality to create and manage packs of data, authenticate users, and upload content to Pinecone for vector search capabilities.

## Features

- User authentication via a local Flask API
- Create, view, and delete packs
- Upload data from multiple sources:
  - Web pages
  - Local files (CSV, TXT)
  - AWS S3 buckets
- Process and store data in Pinecone vector database

## Configuration

The application requires several environment variables to be set:

1. `API_URL` - URL of the authentication API (default: 'http://localhost:5000')
2. AWS credentials for S3 and Lambda access (stored in Streamlit secrets)

## Getting Started

1. Make sure the Flask API is running:
   ```
   cd /path/to/api
   python app.py
   ```

2. Run the Streamlit application:
   ```
   streamlit run streamlit_app.py
   ```

3. Access the application in your browser at http://localhost:8501

## Using the Application

1. Log in with your username and password
2. Choose an action: Create Pack or Delete Pack
3. When creating a pack:
   - Enter a pack name and description
   - Select a data source (webpage, local file, or S3)
   - Add data to your pack
   - Upload data to Pinecone

## API Integration

This application now uses a local Flask API for authentication and pack management. The API endpoints used are:
- `/login` - For user authentication
- `/user/packs` - For listing and creating packs
- `/user/packs/<pack_id>` - For deleting specific packs

The application still uses AWS Lambda for Pinecone interactions. 