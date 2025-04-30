
# 🧩 Pipeline de vectorisation de documents PDF avec LangChain + Qdrant

Ce projet part d’un dossier `resultats_pdf` généré par **MinerU** (outil d’extraction de contenus PDF) pour créer des chunks, les vectoriser et les stocker dans une base Qdrant. Ensuite, on teste la pertinence des réponses retournées.

---

# 🧩 Création de chunks & import dans Qdrant

> **Contexte**  
> Le dossier `resultats_pdf/` est produit par MinerU (extraction des PDF).  
> On s’en sert pour découper le texte, vectoriser, puis tester rapidement la base.

---

## 1. Générer les chunks en JSON

| Étape | Script | Détail |
|-------|--------|--------|
| Découpage | `make_chunks.py` | Parcourt `resultats_pdf/`, s’appuie sur l’arborescence + les fichiers terminant par `_content_list.json`. |
| Sortie | – | `enriched_chunks_all.json` |
| À faire | – | **Formatter le JSON “à la Eric”** et, dans un second temps, gérer les descriptions d’images. |

---

## 2. Embeddings ⚙️ → Qdrant

| Étape | Script | Détail |
|-------|--------|--------|
| Vectorisation + envoi | `insertion_qdrant.py` | Lit `enriched_chunks_all.json`, génère les embeddings, pousse le tout dans Qdrant. |

> **URL Qdrant**  
> ‑ Sous Docker : `http://host.docker.internal:6333`  
> ‑ Hors Docker : `http://localhost:6333`

---

## 3. Ping‑pong rapide avec la BDD

| Étape | Script | Détail |
|-------|--------|--------|
| Test de pertinence | `interroger_bdd.py` | Envoie une question (sans LLM) et affiche les réponses pour vérifier l’alignement sujet/réponse. |

---

## 📝 Notes

* Le dossier `resultats_pdf/` est plutôt lourd ; si besoin on peut le « light‑washer » pour ne garder que l’arborescence et les `_content_list.json`.
* Pas d’LLM dans la boucle de test : on veut juste valider que les embeddings retombent sur leurs pattes.

---