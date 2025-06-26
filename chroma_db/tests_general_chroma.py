# from chroma_db.chroma_vector_db import ChromaVectorDB
# just for testing
# sample_data = [
#    {"hash": "abc123", "text": "This is a test abstract about AI."},
#    {"hash": "def456", "text": "Another text about climate and research."}
# ]

# db = ChromaVectorDB()
# status = db.store_embeddings(sample_data)

# print(f"Status code: {status}")
# print(f"Total documents in Chroma: {db.count_documents()}")

from llm.Embeddings import embed_user_profile
from chroma_db.chroma_vector_db import chroma_db
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from chroma_db.chroma_vector_db import chroma_db
# from llm.Agent import trigger_agent

# response = trigger_agent("update_papers(['large language models'])")
# print(response['messages'][-1].content)

# from chroma_db.chroma_vector_db import chroma_db

# print("Número de documentos guardados en Chroma:", chroma_db.count_documents())


# Simula el perfil del usuario con un tema relevante
profile_text = "I am interested in climate change and biodiversity research."
embedding = embed_user_profile(profile_text)

# Busca los 5 papers más similares
similar_ids = chroma_db.perform_similarity_search(k=5, user_profile_embedding=embedding)

# Resultado
print("Papers similares encontrados:", similar_ids)
print("Documentos en Chroma desde otro script:", chroma_db.count_documents())
