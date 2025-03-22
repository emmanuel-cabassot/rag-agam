import os
import re
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, Docx2txtLoader, UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader, UnstructuredExcelLoader, UnstructuredRTFLoader,
    JSONLoader, UnstructuredXMLLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import tiktoken

# Charger les variables d'environnement
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("❌ Clé API OpenAI non définie. Vérifiez le fichier .env.")

# Définir le dossier contenant les fichiers
DATA_DIR = "data_small"

# Définition des loaders pour différents formats de fichiers
EXTENSION_LOADERS = {
    ".txt": TextLoader,
    ".csv": CSVLoader,
    ".docx": Docx2txtLoader,
    ".md": UnstructuredMarkdownLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".rtf": UnstructuredRTFLoader,
    ".json": JSONLoader,
    ".xml": UnstructuredXMLLoader
}

print(f"🔍 Recherche de fichiers dans {DATA_DIR}...")
    
documents = []

# Fonction pour extraire le texte et les tableaux d'un PDF avec PyMuPDF
def extract_text_and_tables_pymupdf(pdf_path):
    """ Extrait le texte et les tableaux d'un PDF avec PyMuPDF et nettoie les données. """
    doc = fitz.open(pdf_path)
    full_text = []
    for page in doc:
        text = page.get_text("text")  # Extrait le texte brut
        text = clean_text(text)
        if text.strip():
            full_text.append(text)

    return "\n\n".join(full_text)

# Fonction de nettoyage avancé du texte
def clean_text(text):
    """ Nettoie et reformate le texte extrait d'un PDF """
    # Correction des mots collés
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    # Ajout d'un espace après les tirets de liste
    text = re.sub(r"(?<!\n)-([A-Za-z])", r"- \1", text)

    # Suppression des espaces inutiles avant/après
    text = text.strip()

    # Ajout de sauts de ligne après les titres en majuscules
    text = re.sub(r"(\n[A-Z ]{5,})\n", r"\1\n\n", text)

    return text

# Fonction pour charger un fichier donné
def load_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".pdf":
        text = extract_text_and_tables_pymupdf(filepath)
        return [Document(page_content=text)] if text.strip() else []

    if ext in EXTENSION_LOADERS:
        try:
            loader = EXTENSION_LOADERS[ext](filepath)
            return loader.load()
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {filepath} : {e}")
    
    return []

# Parcourir les fichiers dans le répertoire DATA_DIR
file_count = 0
for root, _, files in os.walk(DATA_DIR):
    for file in files:
        file_count += 1
        filepath = os.path.join(root, file)
        print(f"📄 Chargement du fichier {file_count} : {filepath}")
        loaded_docs = load_file(filepath)
        documents.extend(loaded_docs)

print(f"📂 **Total de documents chargés : {len(documents)}**")

# Fonction pour estimer le nombre de tokens
def estimate_tokens(text, encoding_name="cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

# Étape 1 : Découpage structurel
structured_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],  # Priorité : paragraphes > phrases > mots
    chunk_size=2000,  # Segments larges pour conserver les sections
    chunk_overlap=300  # Conserver du contexte
)

# Étape 2 : Raffinement par tokens
token_splitter = TokenTextSplitter(
    encoding_name="cl100k_base",  # Encodage utilisé par OpenAI
    chunk_size=300,  # Nombre de tokens maximum par chunk
    chunk_overlap=50  # Tokens de chevauchement pour garder du contexte
)

# Découpage hybride
def hybrid_split(documents):
    final_chunks = []
    for doc in documents:
        # Découper en gros chunks basés sur la structure
        large_chunks = structured_splitter.split_text(doc.page_content)
        
        # Raffiner chaque chunk large en chunks basés sur les tokens
        for chunk in large_chunks:
            tokenized_chunks = token_splitter.split_text(chunk)
            for token_chunk in tokenized_chunks:
                final_chunks.append(
                    Document(
                        page_content=token_chunk,
                        metadata={
                            "source": doc.metadata.get("source", "Inconnu"),
                            "page": doc.metadata.get("page", "N/A")
                        }
                    )
                )
    return final_chunks

# Utiliser la fonction sur les documents chargés
split_documents = hybrid_split(documents)

print(f"📂 **Total de segments après découpage : {len(split_documents)}**")
print(f"🔍 Exemple d'un chunk : {split_documents[0].page_content}")
print(f"🔖 Métadonnées associées : {split_documents[0].metadata}")

# Définir le dossier de sortie
OUTPUT_DIR = "chunks_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Trouver le prochain numéro de version disponible
file_number = 1
while os.path.exists(os.path.join(OUTPUT_DIR, f"chunks_{file_number}.txt")):
    file_number += 1

# Définir le chemin du fichier de sortie avec la version
output_file = os.path.join(OUTPUT_DIR, f"chunks_{file_number}.txt")

# Enregistrer les segments dans le fichier
with open(output_file, "w", encoding="utf-8") as f:
    for i, doc in enumerate(split_documents):
        f.write(f"--- Segment {i+1} ---\n")
        f.write(doc.page_content)
        f.write("\n\n")

print(f"✅ Segments enregistrés dans le fichier '{output_file}'.")


# Vérification de l'index FAISS
index_path = "index_agam"
if os.path.exists(index_path):
    print("🛠 Suppression de l'index FAISS existant...")
    os.system(f"rm -r {index_path}")

print("⚠️ Création d'un nouvel index FAISS...")

# Initialiser les embeddings BGE
bge_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en",
    encode_kwargs={'normalize_embeddings': True}
)

# Créer le vectorstore avec les nouveaux embeddings
vectorstore = FAISS.from_documents(split_documents, bge_embeddings)
vectorstore.save_local(index_path)
print("✅ Index FAISS enregistré dans 'index_agam/' !")
