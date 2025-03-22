import os
import re
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("❌ Clé API OpenAI non définie. Vérifiez le fichier .env.")

# Définir le dossier contenant les fichiers PDF
DATA_DIR = "data_small"
EXTRACTION_DIR = "pdf_extractions"

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(EXTRACTION_DIR, exist_ok=True)

print(f"🔍 Recherche de fichiers PDF dans {DATA_DIR}...")

# Fonction pour extraire le texte d'un PDF avec PyMuPDF
def extract_text_pymupdf(pdf_path):
    """ Extrait le texte brut d'un PDF avec PyMuPDF et applique un nettoyage. """
    doc = fitz.open(pdf_path)
    full_text = []
    for page in doc:
        text = page.get_textdict("text")  # Extrait le texte brut
        text = clean_text(text)  # Nettoyage du texte
        if text.strip():
            full_text.append(text)
    return "\n\n".join(full_text)

# Fonction de nettoyage avancé du texte
def clean_text(text):
    """ Nettoie et reformate le texte extrait d'un PDF """
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # Correction des mots collés
    text = re.sub(r"(?<!\n)-([A-Za-z])", r"- \1", text)  # Ajout d'espace après les tirets
    text = text.strip()  # Suppression des espaces inutiles
    text = re.sub(r"(\n[A-Z ]{5,})\n", r"\1\n\n", text)  # Ajout de sauts de ligne après les titres
    return text

# Trouver le prochain numéro de fichier disponible
file_number = 1
while os.path.exists(os.path.join(EXTRACTION_DIR, f"extraction_{file_number}.txt")):
    file_number += 1

# Définir le chemin du fichier de sortie
extraction_file = os.path.join(EXTRACTION_DIR, f"extraction_{file_number}.txt")

# Extraire le texte des PDFs et l'enregistrer
with open(extraction_file, "w", encoding="utf-8") as f:
    file_count = 0
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_count += 1
                filepath = os.path.join(root, file)
                print(f"📄 Extraction du fichier {file_count} : {filepath}")
                extracted_text = extract_text_pymupdf(filepath)
                if extracted_text:
                    f.write(f"--- Fichier : {file} ---\n")
                    f.write(extracted_text)
                    f.write("\n\n")

print(f"✅ Extraction brute des PDFs enregistrée dans '{extraction_file}'.")
#extraction du texte
#pymupdf
#page.gettextdict
#structure les textes
#gettextdict
#spacy 