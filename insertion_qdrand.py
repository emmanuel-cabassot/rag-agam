import os
import json
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# Fonction pour charger le fichier JSON
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Chemin vers le fichier contenant les chunks enrichis
base_dir = "./"
chunks_file = os.path.join(base_dir, "enriched_chunks_all.json")

# Charger les chunks
chunks_data = load_json(chunks_file)

# Convertir les chunks en objets Document de LangChain
documents = []
for chunk in chunks_data:
    doc = Document(page_content=chunk["page_content"], metadata=chunk["metadata"])
    documents.append(doc)

# Initialiser le modèle d'embedding
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Paramètres de connexion à Qdrant
qdrant_url = "http://host.docker.internal:6333"
collection_name = "test_30_04"

# Initialiser le client Qdrant
qdrant_client = QdrantClient(url=qdrant_url)

# Vérifier si la collection existe déjà
collections = qdrant_client.get_collections()
if collection_name in [col.name for col in collections.collections]:
    print(f"La collection '{collection_name}' existe déjà.")
else:
    # Créer une nouvelle collection avec les paramètres appropriés
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Collection '{collection_name}' créée avec succès.")

# Insérer les documents dans la collection Qdrant
vector_store = Qdrant(
    client=qdrant_client,
    collection_name=collection_name,
    embeddings=embedding_model,
)

vector_store.add_documents(documents)

print(f"Les documents ont été ingérés dans la collection '{collection_name}' de Qdrant.")

