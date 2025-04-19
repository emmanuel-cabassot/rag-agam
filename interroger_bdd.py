# Interroger la bdd qdrant
import os
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient

# 💬 Pose ta question ici
query = "Quelle est la place du cinéma à Marseille dans l'économie et l'attractivité du territoire ?"

# 📍 Connexion à Qdrant
qdrant_url = "http://host.docker.internal:6333"
collection_name = "enriched_chunks_collection"

# 🤗 Embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 🔌 Client Qdrant
qdrant_client = QdrantClient(url=qdrant_url)

# 🔍 Création du vector store (lecture seule)
vector_store = Qdrant(
    client=qdrant_client,
    collection_name=collection_name,
    embeddings=embeddings,
)

# 🔎 Recherche vectorielle
docs = vector_store.similarity_search(query, k=5)

# 📋 Affichage des résultats
print("\n--- Résultats de la recherche ---\n")
all_context = ""
for i, doc in enumerate(docs, 1):
    print(f"Résultat {i} :")
    print(doc.page_content.strip()[:1000], "...")  # Petit extrait
    print("📌 Source :", doc.metadata.get("source"))
    print("📖 Titre  :", doc.metadata.get("title"))
    print("📄 Page   :", doc.metadata.get("start_page"))
    print("-" * 60)
    all_context += doc.page_content + "\n"

# 🧠 Synthèse simple à partir du contexte
print("\n--- Synthèse de la réponse (résumé naïf) ---\n")

if all_context:
    print("Tout est afficher correctment")
else:
    print("Aucun contenu pertinent trouvé dans la base vectorielle.")

