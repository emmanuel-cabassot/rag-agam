import gradio as gr
import os
import numpy as np
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.chains import RetrievalQA

# Charger les variables d'environnement
load_dotenv()

# ✅ Charger les embeddings Hugging Face (BAAI/bge-large-en)
bge_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en",
    encode_kwargs={'normalize_embeddings': True}
)

# ✅ Charger l'index FAISS avec les bons embeddings
index_path = "index_agam"
vectorstore = FAISS.load_local(index_path, bge_embeddings, allow_dangerous_deserialization=True)

# ✅ Vérifier la dimension de l'index FAISS
faiss_dim = vectorstore.index.d
print(f"📊 Dimension des vecteurs FAISS : {faiss_dim}")

# ✅ Configurer le modèle LLM Ollama avec DeepSeek-R1
llm = OllamaLLM(
    model="deepseek-r1",
    base_url="http://host.docker.internal:11434",  # URL pour accéder à Ollama depuis le conteneur Docker
    request_timeout=60  # Timeout augmenté à 60 secondes
)


qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever(search_kwargs={"k": 15}))

# ✅ Fonction améliorée pour inclure les sources
def chatbot(question):
    # 🔍 Vérifier la dimension du vecteur de la requête
    query_vector = np.array(bge_embeddings.embed_query(question), dtype=np.float32).reshape(1, -1)
    print(f"📊 Dimension du vecteur de la requête : {query_vector.shape}")

    # 🔍 Récupérer les documents pertinents avec FAISS
    retrieved_docs = vectorstore.similarity_search_by_vector(query_vector[0], k=10)

    if not retrieved_docs:
        return "❌ Aucun document pertinent trouvé."


    # 📄 Construire un texte consolidé à partir des documents récupérés
    retrieved_text = "\n".join(
        f"[{i+1}] {doc.metadata.get('source', 'Source inconnue')}: {doc.page_content}"
        for i, doc in enumerate(retrieved_docs[:10])
    )
    print(f"Retour du FAISS  avant: {retrieved_text}")

    retrieved_text = retrieved_text.replace("•", "").replace("", "").replace("\n\n", "\n").strip()
    print(f"Retour du FAISS après : {retrieved_text}")


    # 🎯 Générer une réponse avec Ollama en incluant les sources
    prompt = (
        f"Tu es un expert en urbanisme et tu as la connaissance de tous les documents.\n"
        f"Réponds précisément à la question posée en t'appuyant uniquement sur les extraits ci-dessous.\n"
        f"N'oublie pas d'ajouter des références aux documents d'où proviennent les informations.\n"
        f"\nExtraits des documents :\n{retrieved_text}\n\n"
        f"Question : {question}\n"
        f"Réponse détaillée avec sources :"
    )

    response = llm.invoke(prompt)

    # ✅ Extraire uniquement le texte généré sans les métadonnées
    print(response)

    return response["choices"][0]["message"]["content"]

# ✅ Interface Gradio améliorée
iface = gr.Interface(
    fn=chatbot,
    inputs="text",
    outputs="text",
    title="Chatbot RAG - AGAM",
    description="Pose une question sur les documents de l'AGAM et obtiens une réponse détaillée avec les sources.",
    theme="default"
)

# ✅ Lancer l'interface avec les paramètres pour Docker
iface.launch(server_name="0.0.0.0", server_port=7860)
