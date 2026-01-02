import chromadb
from ..config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        try:
            from ..utils.custom_embeddings import OllamaEmbeddingFunction
            # Try to get model from settings, fallback to llama3.1
            model_name = getattr(settings, "OLLAMA_MODEL", "llama3.1")
            # Clean model name if it has tag (sometimes ollama.embeddings needs clean name? strictness varies)
            # But simple pass through is usually fine.
            
            ef = OllamaEmbeddingFunction(model_input=model_name)
            
            self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_DIR)
            self.collection = self.client.get_or_create_collection(
                name="query_expertise",
                embedding_function=ef
            )
            logger.info(f"✅ ChromaDB initialized with Ollama embeddings (model: {model_name})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            self.collection = None

    def add_expertise(self, query: str, sql: str, schema: str, dataset_id: int, user_id: int):
        """Store a successful (query, sql, schema) triplet for RAG"""
        if not self.collection:
            return False
            
        try:
            metadata = {
                "sql": sql,
                "schema": schema,
                "dataset_id": dataset_id,
                "user_id": user_id
            }
            # Use unique ID to avoid overwriting unless intended
            entry_id = str(uuid.uuid4())
            
            self.collection.add(
                documents=[query],
                metadatas=[metadata],
                ids=[entry_id]
            )
            logger.info(f"💾 Added expertise for dataset {dataset_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding expertise: {e}")
            return False

    def get_related_expertise(self, query: str, dataset_id: int, limit: int = 3):
        """Retrieve similar past queries to use as few-shot examples in prompts"""
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where={"dataset_id": dataset_id}
            )
            
            expertise_list = []
            if results and results.get('documents') and len(results['documents']) > 0:
                for idx, doc in enumerate(results['documents'][0]):
                    expertise_list.append({
                        "query": doc,
                        "sql": results['metadatas'][0][idx]['sql'],
                        # We don't necessarily need schema in the prompt if it's the same, 
                        # but good to have for multi-schema context.
                    })
            return expertise_list
        except Exception as e:
            logger.error(f"❌ Error retrieving expertise: {e}")
            return []

    def list_expertise(self, user_id: int = None, dataset_id: int = None):
        """List expertise, optionally filtered by user or dataset"""
        if not self.collection:
            return []
        
        try:
            where_clause = {}
            if user_id: where_clause["user_id"] = user_id
            if dataset_id: where_clause["dataset_id"] = dataset_id
            
            results = self.collection.get(
                where=where_clause if where_clause else None
            )
            
            expertise_list = []
            if results and results.get('documents'):
                for idx, doc in enumerate(results['documents']):
                    expertise_list.append({
                        "id": results['ids'][idx],
                        "query": doc,
                        "sql": results['metadatas'][idx]['sql'],
                        "dataset_id": results['metadatas'][idx]['dataset_id'],
                        "user_id": results['metadatas'][idx].get('user_id')
                    })
            return expertise_list
        except Exception as e:
            logger.error(f"❌ Error listing expertise: {e}")
            return []

    def delete_expertise(self, entry_id: str):
        """Remove an entry from the knowledge base"""
        if not self.collection:
            return False
        try:
            self.collection.delete(ids=[entry_id])
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting expertise: {e}")
            return False

knowledge_service = KnowledgeService()
