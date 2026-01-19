import pyodbc
import json
import os
from pathlib import Path
from langchain_core.documents import Document
def create_sql_connection():
    """
    Connects to the SQL Server database and returns the connection object.
    """
    try:
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=IN-MANISH-KUMAR\SQLEXPRESS;'
            r'DATABASE=CustomerShopping;'
            r'Trusted_Connection=yes;'
        )
        # Return the connection object, not the cursor
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print("Error connecting to database:", e)
        return None
    
from opensearchpy import OpenSearch

def create_opensearch_client():
    """
    Creates and returns an OpenSearch client. Checks if the connection is established.
    Returns:
        OpenSearch client if connection is successful, None otherwise.
    """
    try:
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=False,
            verify_certs=False
        )
        # Check connection
        if client.ping():
            print("Connected to OpenSearch successfully!")
            return client
        else:
            print("Failed to connect to OpenSearch.")
            return None
    except Exception as e:
        print(f"Error connecting to OpenSearch: {e}")
        return None
    
create_opensearch_client()

def apply_jq_schema(json_data, jq_schema='.'): 
    data = json.loads(json_data)
    if jq_schema == '.' or jq_schema.strip() == '':
        return json.dumps(data)
    # Remove leading dot and split by '.'
    keys = jq_schema.lstrip('.').split('.')
    for key in keys:
        if key:
            if isinstance(data, dict):
                data = data.get(key, None)
            else:
                data = None
            if data is None:
                raise ValueError(f"Key '{key}' not found in JSON data")
    return json.dumps(data)

def load_json_data(file_path, jq_schema='.', text_content=False, json_lines=True):
    file_path = Path(file_path).resolve()
    documents = []
    
    with open(file_path, 'r') as file:
        for line in file:
            # Apply jq schema to each line/document
            filtered_data = apply_jq_schema(line, jq_schema)
            # Construct metadata for each document
            metadata = {'source': str(file_path), 'seq_num': len(documents) + 1}
            # Create a Document object and append it to the documents list
            documents.append(Document(page_content=filtered_data, metadata=metadata))
    
    return documents