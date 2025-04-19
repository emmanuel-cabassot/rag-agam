# Prend le dossier rendu par minerU pour en faire des chunks au format json
# Fichier de sortie : enriched_chunks_all.json
import os
import json
from bs4 import BeautifulSoup

# Paramètres généraux
# Chemin du dossier principal contenant les fichiers JSON générés par minerU
# Les fichiers doivent suivre le format *_content_list.json
# MIN_SIZE et MAX_SIZE contrôlent la taille minimale et maximale des chunks créés

# Paramètres
dossier_principal = "./resultats_pdf/Envoi Métropole livrables 2023"
MIN_SIZE = 512
MAX_SIZE = 1024

### ------------------- Fonctions -------------------- ###

def load_json(file_path):
    # Charge un fichier JSON et retourne son contenu
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Transforme un tableau HTML en tableau Markdown (lisible dans du texte brut)
def html_table_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return html
    rows = []
    for tr in table.find_all("tr"):
        row = []
        headers = tr.find_all("th")
        if headers:
            row = [th.get_text(strip=True) for th in headers]
        else:
            row = [td.get_text(strip=True) for td in tr.find_all("td")]
        if row:
            rows.append(row)
    if not rows:
        return ""
    md_table = []
    header_row = rows[0]
    md_table.append("| " + " | ".join(header_row) + " |")
    md_table.append("|" + "|".join([" --- " for _ in header_row]) + "|")
    for row in rows[1:]:
        md_table.append("| " + " | ".join(row) + " |")
    return "\n".join(md_table)

# Rend le contenu d'un item en fonction de son type : texte ou tableau
def render_item_content(item):
    chunk_type = item.get("type", "text")
    if chunk_type == "text":
        return item.get("text", "").strip()
    elif chunk_type == "table":
        body = item.get("table_body", "").strip()
        md_table = html_table_to_markdown(body)
        caption = " ".join(item.get("table_caption", []))
        footnote = " ".join(item.get("table_footnote", []))
        return f"TABLE\nCaption: {caption}\nFootnote: {footnote}\nTable:\n{md_table}"
    else:
        return ""

# Nettoie un titre de chunk en conservant uniquement la partie pertinente
# Si le titre contient plusieurs niveaux (séparés par des /), on garde le dernier si les précédents ne sont pas présents dans le texte
def clean_chunk_title(chunk_title, page_content):
    titles = [t.strip() for t in chunk_title.split("/")]
    missing_titles = [t for t in titles if t not in page_content]
    if not missing_titles:
        return chunk_title
    return titles[-1]

# ----------------- Traitement principal ----------------- #

all_chunks = []

# Parcourt récursivement tous les fichiers du dossier principal
for root, dirs, files in os.walk(dossier_principal):
    for file in files:
        if file.endswith("_content_list.json"):

            content_list_path = os.path.join(root, file)
            source_filename = os.path.relpath(root, dossier_principal).replace("/auto", "") + ".pdf"

            print(f"📄 Traitement du fichier : {content_list_path}")

            content_list = load_json(content_list_path)

            chunk_header = ""
            current_chunk_body = []
            current_chunk_start_page = None

            for item in content_list:
                chunk_type = item.get("type", "text")
                if chunk_type == "image":
                    continue

                page_idx = item.get("page_idx")

                # Nouveau titre de section de niveau 1 = début d'un nouveau chunk
                if chunk_type == "text" and item.get("text_level") == 1:
                    new_title = item.get("text", "").strip()

                    # Si le chunk en cours est trop petit, on fusionne avec le suivant
                    if current_chunk_body and len("\n".join(current_chunk_body)) < MIN_SIZE:
                        chunk_header = chunk_header + " / " + new_title if chunk_header else new_title
                        current_chunk_body[0] = chunk_header
                    else:
                        if current_chunk_body:
                            finalized = {
                                "page_content": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)) + "\n\n" + "\n".join(current_chunk_body),
                                "metadata": {
                                    "source": source_filename,
                                    "title": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)),
                                    "start_page": current_chunk_start_page
                                }
                            }
                            all_chunks.append(finalized)
                        chunk_header = new_title
                        current_chunk_start_page = page_idx
                        current_chunk_body = [chunk_header]
                else:
                    content = render_item_content(item)
                    if not content:
                        continue
                    if not current_chunk_body:
                        current_chunk_start_page = page_idx
                        chunk_header = ""
                    candidate = "\n".join(current_chunk_body + [content])

                    # Si le contenu dépasse la taille max autorisée, on coupe et on enregistre le chunk
                    if len(candidate) > MAX_SIZE and len("\n".join(current_chunk_body)) >= MIN_SIZE:
                        finalized = {
                            "page_content": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)) + "\n\n" + "\n".join(current_chunk_body),
                            "metadata": {
                                "source": source_filename,
                                "title": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)),
                                "start_page": current_chunk_start_page
                            }
                        }
                        all_chunks.append(finalized)
                        current_chunk_body = [content.strip()]
                        current_chunk_start_page = page_idx
                        chunk_header = ""
                    else:
                        current_chunk_body.append(content)

            # Ne pas oublier le dernier chunk si jamais on atteint la fin du fichier
            if current_chunk_body:
                finalized = {
                    "page_content": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)) + "\n\n" + "\n".join(current_chunk_body),
                    "metadata": {
                        "source": source_filename,
                        "title": clean_chunk_title(chunk_header, "\n".join(current_chunk_body)),
                        "start_page": current_chunk_start_page
                    }
                }
                all_chunks.append(finalized)

# Écriture de tous les chunks dans un seul fichier de sortie JSON
output_file = "enriched_chunks_all.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

print(f"\n✅ Tous les chunks ont été regroupés dans '{output_file}' ({len(all_chunks)} chunks créés au total).")
