import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class VectorService:
    """
    Service for Vector DB operations using ChromaDB.
    Used for RAG (Retrieval Augmented Generation) to ground the LLM.
    """
    
    def __init__(self, persist_directory: str = "vector_db"):
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"✅ ChromaDB client initialized at {self.persist_directory}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise e

        # Initialize Embedding Function (Sentence Transformers)
        # Using a small, fast model suitable for running on CPU/Mac
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            logger.info("✅ Embedding function initialized (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding function: {e}")
            # Fallback or raise? For now, we need this.
            raise e

    def get_collection(self, name: str):
        """Get or create a collection"""
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )

    def store_schema_context(self, dataset_id: str, schema_text: str, column_metadata: List[Dict[str, Any]]):
        """
        Store schema context chunks for a dataset.
        
        Args:
            dataset_id: Unique identifier for the dataset
            schema_text: Full text description of the schema
            column_metadata: List of dicts with column info to be chunked/embedded
        """
        collection_name = f"dataset_{dataset_id}_schema"
        collection = self.get_collection(collection_name)
        
        documents = []
        metadatas = []
        ids = []
        
        # 1. Add the full schema summary as one chunk
        documents.append(schema_text)
        metadatas.append({"type": "full_schema", "dataset_id": dataset_id})
        ids.append(f"{dataset_id}_full_schema")
        
        # 2. Add individual column chunks for fine-grained retrieval
        for col in column_metadata:
            # Create a rich description for the column
            col_name = col.get("name", "unknown")
            col_type = col.get("type", "unknown")
            desc = f"Column: {col_name}\nType: {col_type}\n"
            if "description" in col:
                desc += f"Description: {col['description']}\n"
            if "stats" in col:
                desc += f"Stats: {col['stats']}\n"
            if "samples" in col:
                desc += f"Samples: {col['samples']}\n"
                
            documents.append(desc)
            metadatas.append({"type": "column_def", "col_name": col_name, "dataset_id": dataset_id})
            ids.append(f"{dataset_id}_col_{col_name}")
            
        # Upsert to ChromaDB
        try:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Stored {len(documents)} schema chunks for dataset {dataset_id}")
        except Exception as e:
            logger.error(f"❌ Failed to upsert schema to ChromaDB: {e}")

    def retrieve_context(self, dataset_id: str, query: str, n_results: int = 5) -> List[str]:
        """
        Retrieve relevant schema context for a user query.
        """
        collection_name = f"dataset_{dataset_id}_schema"
        try:
            # Check if collection exists
            try:
                collection = self.client.get_collection(
                    name=collection_name, 
                    embedding_function=self.embedding_fn
                )
            except ValueError:
                logger.warning(f"Collection {collection_name} not found.")
                return []

            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Chroma returns a list of lists (one per query)
            if results and results['documents']:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            return []

    def delete_dataset_context(self, dataset_id: str):
        """Delete vector data for a dataset"""
        collection_name = f"dataset_{dataset_id}_schema"
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"🗑️ Deleted collection {collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete collection {collection_name}: {e}")

    def add_vector(self, collection_name: str, vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """
        Generic method to add a single vector to a collection.
        Used by QueryPatternService.
        """
        try:
            collection = self.get_collection(collection_name)
            collection.upsert(
                ids=[vector_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            # logger.info(f"✅ Stored vector {vector_id} in {collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to add vector to {collection_name}: {e}")
            raise e

    def search(self, collection_name: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Generic method to search a collection using an embedding.
        Used by QueryPatternService.
        """
        try:
            # Check if collection exists first to avoid error
            try:
                collection = self.client.get_collection(
                    name=collection_name, 
                    embedding_function=self.embedding_fn
                )
            except ValueError:
                logger.warning(f"Collection {collection_name} not found during search.")
                return []

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['metadatas', 'documents', 'distances']
            )

            # Parse results into a clean list of dicts
            parsed_results = []
            if results and results['ids'] and len(results['ids']) > 0:
                # Iterate through the first query's results
                for i in range(len(results['ids'][0])):
                    item = {
                        "id": results['ids'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "document": results['documents'][0][i] if results['documents'] else "",
                        "distance": results['distances'][0][i] if results['distances'] else 0.0
                    }
                    parsed_results.append(item)
            
            return parsed_results

        except Exception as e:
            logger.error(f"❌ Search failed for {collection_name}: {e}")
            return []

# Singleton instance
vector_service = VectorService(persist_directory=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_db"))
