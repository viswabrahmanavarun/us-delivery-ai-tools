from dotenv import load_dotenv
load_dotenv()
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from .data_loader import load_knowledge_base

class RAGSystem:
    def __init__(self):
        self.docs = load_knowledge_base()
        # Initialize free local embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.doc_embeddings = []
        self._initialize_embeddings()
        
    def _get_embedding(self, text):
        return self.model.encode(text)
        
    def _initialize_embeddings(self):
        for doc in self.docs:
            emb = self._get_embedding(doc['content'])
            self.doc_embeddings.append(emb)
            
    def retrieve_relevant_doc(self, query: str, top_k=1):
        query_emb = self._get_embedding(query)
        similarities = [self._cosine_similarity(query_emb, doc_emb) for doc_emb in self.doc_embeddings]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        if similarities[top_indices[0]] < 0.2:
            return None
            
        return self.docs[top_indices[0]]
        
    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

_rag_instance = None
def get_rag_system():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance
