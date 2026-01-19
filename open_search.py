import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from opensearchpy import OpenSearch
from langchain_community.vectorstores import OpenSearchVectorSearch
from utility import load_json_data

VM_IP = 'localhost'
PORT = '9200'
PROJECT_ID = "statspeak-484706"
MODEL = "text-embedding-005"
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(current_dir, "credentials", "key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path


EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(model=MODEL, project=PROJECT_ID)
DOCUMENT = load_json_data(file_path='knowledge_base\customer_shopping_data_columns.jsonl')


def get_opensearch_client(vm_ip=VM_IP, port=PORT, http_auth=("admin", "admin")):
    return OpenSearch(
        hosts=[{'host': vm_ip, 'port': int(port)}],
        http_auth=http_auth,
        use_ssl=False,
        verify_certs=False
    )

def ensure_index(client, index_name = "statspeak"):
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

client = get_opensearch_client()

def create_docsearch(documents = DOCUMENT, embedding_model=EMBEDDING_MODEL, vm_ip=VM_IP, port=PORT, index_name="statspeak", engine="faiss", http_auth=("admin", "admin"), use_ssl=False, verify_certs=False,client = client):
    """
    Creates and returns an OpenSearchVectorSearch instance.
    """
    ensure_index(client)
    return OpenSearchVectorSearch.from_documents(
        documents,
        embedding_model,
        opensearch_url=f'http://{vm_ip}:{port}',
        index_name=index_name,
        engine=engine,
        http_auth=http_auth,
        use_ssl=use_ssl,
        verify_certs=verify_certs,
    )
docsearch = create_docsearch()

def get_columns(question, docsearch = docsearch):
    response = docsearch.similarity_search(question, k=7)
    columns = []
    for data in response:
        data = json.loads(data.page_content)
        columns.append({"column_name": data['column_name'], "description": data['description']})
    return columns