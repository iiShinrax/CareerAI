import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

class JobRAG:
    def __init__(self, vector_db_dir="vector_db", model_name="all-MiniLM-L6-v2"):
        print("⏳ جاري ربط الذاكرة الوظيفية (RAG Vector DB)...")
        
        # تحديد مسارات الملفات اللي سواها زميلك
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.index_path = os.path.join(base_dir, vector_db_dir, "index.faiss")
        self.metadata_path = os.path.join(base_dir, vector_db_dir, "metadata.json")
        
        # تحميل المودل والفهرس
        self.model = SentenceTransformer(model_name)
        self.index = faiss.read_index(self.index_path)
        
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
    def search_job(self, job_title, top_k=3):
        """تبحث عن الوظيفة وترجع أهم المهارات والمهام الخاصة فيها"""
        # تحويل اسم الوظيفة لأرقام (Vector)
        query_vector = self.model.encode([job_title], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        
        # البحث في FAISS
        distances, indices = self.index.search(query_vector, top_k)
        
        # تجميع النتائج
        context_chunks = []
        for idx in indices[0]:
            if idx != -1:
                context_chunks.append(self.metadata[idx]["text"])
                
        return "\n\n".join(context_chunks)