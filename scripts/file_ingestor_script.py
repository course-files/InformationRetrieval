import base64
import requests
import json
import sys
import os

ES_HOST = "http://localhost:9200"
PIPELINE_NAME = "file_ingestor"
INDEX_NAME = "public_health_index"

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def upload_to_elasticsearch(file_path):
    encoded_content = encode_file_to_base64(file_path)
    doc_id = os.path.splitext(os.path.basename(file_path))[0]
    payload = {
        "filename": os.path.basename(file_path),
        "data": encoded_content
    }
    url = f"{ES_HOST}/{INDEX_NAME}/_doc/{doc_id}?pipeline={PIPELINE_NAME}"
    headers = {"Content-Type": "application/json"}
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    print(f"Indexing {os.path.basename(file_path)} - Status Code: {response.status_code}")
    print("Response:", response.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python file_ingestor_script.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]

    if not os.path.isdir(directory_path):
        print("Error: Directory does not exist.")
        sys.exit(1)

    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            upload_to_elasticsearch(file_path)

    print("Finished processing PDF files.")
