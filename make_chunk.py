import re

def load_markdown(file_path):
    """Lit le fichier Markdown et retourne le texte brut."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_markdown(md_text):
    """
    Parse le texte markdown en détectant les en-têtes.
    On considère que les lignes commençant par '#' sont des titres.
    Retourne le titre principal et une liste de sections, chacune ayant un titre, un niveau et un contenu.
    """
    lines = md_text.splitlines()
    sections = []
    current_section = None
    main_title = None

    for line in lines:
        heading_match = re.match(r'^(#+)\s+(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            # Le premier titre de niveau 1 sera le titre principal
            if level == 1 and main_title is None:
                main_title = title
                current_section = {"title": title, "level": level, "content": ""}
            else:
                # Avant de passer à une nouvelle section, sauvegarder la précédente
                if current_section is not None:
                    sections.append(current_section)
                current_section = {"title": title, "level": level, "content": ""}
        else:
            # Ajouter la ligne au contenu de la section en cours
            if current_section is None:
                # Si aucun titre n'a été rencontré, on crée une section par défaut
                current_section = {"title": "", "level": 0, "content": line + "\n"}
            else:
                current_section["content"] += line + "\n"
    if current_section is not None:
        sections.append(current_section)
    return main_title, sections

def split_text_into_chunks(text, min_size=300, max_size=600):
    """
    Découpe un texte en sous-parties dont la longueur est comprise entre min_size et max_size.
    On essaie de découper par phrases en utilisant le séparateur '. '.
    """
    text = text.strip()
    if len(text) <= max_size:
        return [text]
    
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Reconstituer la phrase avec le point perdu par le split
        if current_chunk:
            candidate = current_chunk + ". " + sentence
        else:
            candidate = sentence
        if len(candidate) > max_size:
            # Si le chunk courant est suffisamment long, on le sauvegarde
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Sinon, on accepte d'ajouter cette phrase malgré le dépassement
                current_chunk = candidate
        else:
            current_chunk = candidate
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

def create_chunks_from_sections(main_title, sections, min_size=300, max_size=600):
    """
    Pour chaque section, découpe son contenu en chunks et préfixe chaque chunk avec
    le titre principal et le titre de la section courante.
    """
    chunks = []
    current_section_title = main_title
    for section in sections:
        # Si la section est un titre de niveau 1, on met à jour le titre de la section
        if section["level"] == 1:
            current_section_title = section["title"]
        content = section["content"].strip()
        if not content:
            continue
        section_chunks = split_text_into_chunks(content, min_size, max_size)
        for chunk in section_chunks:
            # Chaque chunk est préfixé par le titre principal et le titre de la section
            full_chunk = f"{main_title}\n{current_section_title}\n{chunk}"
            chunks.append(full_chunk)
    return chunks

# --- Main ---
# Charger le fichier Markdown
md_text = load_markdown("test_man.md")

# Parser le markdown pour obtenir le titre principal et les sections
main_title, sections = parse_markdown(md_text)

# Créer les chunks à partir des sections
chunks = create_chunks_from_sections(main_title, sections)

# Regrouper tous les chunks dans un document unique en les séparant par un délimiteur
output_document = "\n\n---\n\n".join(chunks)

# Sauvegarder le résultat dans un fichier "output_document.txt"
with open("output_document.txt", "w", encoding="utf-8") as f:
    f.write(output_document)

print("Le document de chunks a été enregistré dans 'output_document.txt'")
