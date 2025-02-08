import os
import re
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, Docx2txtLoader, UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader, UnstructuredExcelLoader, UnstructuredRTFLoader,
    JSONLoader, UnstructuredXMLLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

# Charger les variables d'environnement
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("❌ Clé API OpenAI non définie. Vérifiez le fichier .env.")

# Définir le dossier contenant les fichiers
DATA_DIR = "data"

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
    tables = []

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

# Afficher un extrait des documents avant le split
print("\n🔍 **Exemple de texte extrait :**")
print(documents[0].page_content[:1000])

# Ajout du Text Splitter avec une meilleure configuration
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,  # Segments plus longs pour plus de contexte
    chunk_overlap=200
)

split_documents = text_splitter.split_documents(documents)
print(f"📂 **Total de segments après découpage : {len(split_documents)}**")

# Enregistrement des segments dans un fichier texte unique
output_file = "documents_transformes.txt"
with open(output_file, "w", encoding="utf-8") as f:
    for i, doc in enumerate(split_documents):
        f.write(f"--- Segment {i+1} ---\n")
        f.write(doc.page_content)
        f.write("\n\n")

print(f"✅ Segments enregistrés dans le fichier '{output_file}'.")

# Vérification de l'index FAISS
index_path = "index_agam"

# Suppression et recréation complète de l'index FAISS
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

# Vérifier le nombre de vecteurs dans l'index
print(f"🔍 Nombre de vecteurs dans l'index FAISS : {vectorstore.index.ntotal}")

# Test de récupération et génération de réponse
print("\n🔍 Test du système RAG...")

# Nouvelle question pour tester le système
query = "Quels sont les défis et opportunités pour l'industrie du cinéma à Marseille ?"

# Augmentation du nombre de documents récupérés (k=15)
retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

# Initialiser le modèle LLM
llm = ChatOpenAI(api_key=openai_api_key, model_name="gpt-4", temperature=0, request_timeout=15)

# Créer la chaîne de récupération QA
qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)

# Récupérer les documents pertinents
retrieved_docs = retriever.get_relevant_documents(query)
cleaned_text = "\n".join(doc.page_content for doc in retrieved_docs).strip()

# Générer la réponse
response = llm.invoke([HumanMessage(content=f"En te basant uniquement sur ces extraits, résume les défis et opportunités du cinéma à Marseille :\n\n{cleaned_text}")])

print("\n📝 Réponse générée par l'IA :")
print(response.content)
