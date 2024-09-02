import os
from qdrant_client import QdrantClient


os.environ['OPENAI_API_KEY'] = 'your-openai-apikey'


qdrant_client = QdrantClient(
    url="add67a69-43d5-4bd9-b72b-194eba28b90a.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key=os.environ["AfCEWmPdM17JABsezQ45-ANIze_GvAf95vGv57dtpHaSpsZcDP-5ng"],
)
