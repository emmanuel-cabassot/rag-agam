import os
import json
from bs4 import BeautifulSoup

# Paramètres de taille (en nombre de caractères)
MIN_SIZE = 512
MAX_SIZE = 1024

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

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

chunk_header = ""
current_chunk_body = []
current_chunk_start_page = None
chunks = []

def clean_chunk_title(chunk_title, page_content):
    titles = [t.strip() for t in chunk_title.split("/")]
    missing_titles = [t for t in titles if t not in page_content]
    if not missing_titles:
        return chunk_title
    return titles[-1]

def finalize_chunk():
    if not current_chunk_body or not chunk_header:
        return None

    body = "\n".join(current_chunk_body)
    real_title = clean_chunk_title(chunk_header, body)

    return {
        "page_content": real_title + "\n\n" + body,
        "metadata": {
            "source": source_filename,
            "title": real_title,
            "start_page": current_chunk_start_page
        }
    }

base_dir = "./test_pour_extraction/auto"
content_list_path = os.path.join(base_dir, "OTLE 2023_Logement Etudiant AMP_Synthèse_2023_content_list.json")
source_filename = "OTLE 2023_Logement Etudiant AMP_Synthèse_2023_origin.pdf"

content_list = load_json(content_list_path)

for item in content_list:
    chunk_type = item.get("type", "text")
    if chunk_type == "image":
        continue

    page_idx = item.get("page_idx")

    if chunk_type == "text" and item.get("text_level") == 1:
        new_title = item.get("text", "").strip()

        if current_chunk_body and len("\n".join(current_chunk_body)) < MIN_SIZE:
            if chunk_header:
                chunk_header = chunk_header + " / " + new_title
                current_chunk_body[0] = chunk_header
            else:
                chunk_header = new_title
                current_chunk_body.insert(0, new_title)
        else:
            if current_chunk_body:
                finalized = finalize_chunk()
                if finalized:
                    chunks.append(finalized)
                current_chunk_body = []
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

        if len(candidate) > MAX_SIZE and len("\n".join(current_chunk_body)) >= MIN_SIZE:
            finalized = finalize_chunk()
            if finalized:
                chunks.append(finalized)
            current_chunk_body = []
            current_chunk_start_page = page_idx
            chunk_header = ""
            current_chunk_body.append(content.strip())
        else:
            current_chunk_body.append(content)

finalized = finalize_chunk()
if finalized:
    chunks.append(finalized)

output_file = os.path.join(base_dir, "enriched_chunks.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"Les chunks ont été créés et sauvegardés dans '{output_file}'")
