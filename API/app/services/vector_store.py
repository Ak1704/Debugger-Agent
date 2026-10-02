import chromadb
from app.config import settings
from app.services.embeddings import CodeEmbeddings

class CodeVectorStore:
    def __init__(self):
        self.embedder = CodeEmbeddings()
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection("code_units")

    def add(self, ids, texts, metadatas):
        vectors = self.embedder.embed_documents(texts)
        self.collection.upsert(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)

    def search(self, query: str, n_results=5, where=None):
        vector = self.embedder.embed_query(query)
        return self.collection.query(query_embeddings=[vector], n_results=n_results, where=where)
