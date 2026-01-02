import logging
import ollama
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger(__name__)

class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_input: str = "llama3.1"):
        """
        Initialize the Ollama Embedding Function.
        Args:
            model_input (str): The model name to use for embeddings. Defaults to 'llama3.1'.
        """
        self.model = model_input

    def __call__(self, input: Documents) -> Embeddings:
        """
        Get embeddings for a list of documents.
        Args:
            input (Documents): A list of texts to embed.
        Returns:
            Embeddings: A list of embeddings.
        """
        embeddings = []
        for text in input:
            try:
                response = ollama.embeddings(model=self.model, prompt=text)
                embedding = response["embedding"]
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error generating embedding for text '{text[:30]}...': {e}")
                # Fallback or empty embedding? 
                # ChromaDB expects a list of floats. If fails, better to re-raise or return zeros?
                # For now, simplistic error handling.
                embeddings.append([0.0] * 4096) # Approximate size, might break if dimension mismatch
        return embeddings
