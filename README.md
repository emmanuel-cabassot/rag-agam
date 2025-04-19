# Créer des chunks et les mettre en BBD
A partir du dossier resultats_pdf qui est le resultat de minerU (extraction de pdf)
1. créer des chunks en json
2. Modifier ces chunks pour les vectoriser et les envoyer en BDD qdrant
3. Interroger succintement la BDD pour voir si elle renvoie des reponses alignés avec le sujet de la question


1. créer des chunks en json
On utilise le script make_chunks.py
Il prend le dossier resultats_pdf pour en faire des chunks
Le résultat est le fichier enriched_chunks_all.json
Il se sert principalement de l'arborescence et du fichier terminant par _content_list.json
Pour la suite :
Formater le json au format Eric.
Le reste des fichiers sont pour l'instant superflues, mais dans un deuxième temps il faudra gérer la description des images

2. Modifier ces chunks pour les vectoriser et les envoyer en BDD qdrant
On utilise le script insertion_qdrand.py
Il prend le fichier enriched_chunks_all.json (chunks formatés en json)
Il crée les embeddings et envoie tout cela en BDD qdrant

3. Interroger succintement la BDD pour voir si elle renvoie des reponses alignés avec le sujet de la question
On utilise le script interroger_bdd.py
Pas de llm utiliser juste une question et des réponses pour tester la pertinence

ps : 
Pour se lier à qdrant à la place de http://lochalhost::6333 on utilise http://host.docker.internal:6333 car on part d'un environnment docker. Donc si vous n'êtes pas sur Docker il faudra utiliser localhost.

le dossier resultats_pdf est le resultat de minerU
Il ne sera pas forcement présent dans ce dossier car assez lourd. Je pourrais le nettoyer pour n'en ressortir que l'arborescence et le fichier _content_list.json.

