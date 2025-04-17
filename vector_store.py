"""
Vector Store Module
Manages the FAISS vector database for storing and retrieving document embeddings.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import faiss
import compat_hf
import huggingface_hub

# Inject the shim so other packages using huggingface_hub.cached_download won’t crash
huggingface_hub.cached_download = compat_hf.cached_download
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("semantic_search")

class VectorStore:
    """Class to manage the vector database for document embeddings"""
    
    def __init__(self, db_path: str):
        """Initialize the vector store with the path to the database"""
        self.db_path = Path(db_path)
        self.index_path = self.db_path / "faiss_index.bin"
        self.metadata_path = self.db_path / "document_metadata.json"
        
        # Create the database directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize the embedding model
        local_model_path = "./all-MiniLM-L6-v2"

        self.model = SentenceTransformer(local_model_path)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = None
        self.document_metadata = {}
        
        # Load existing index if available
        self._load_index()
    
    def is_initialized(self) -> bool:
        """Check if the vector store has been initialized with documents"""
        return self.index is not None and len(self.document_metadata) > 0
    
    def reload_index(self):
        return self._load_index()
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document dictionaries with at least 'content' and 'path' fields
        """
        if not documents:
            return
            
        # Create a new index if one doesn't exist yet
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Generate embeddings for all documents
        texts = [doc['content'] for doc in documents]
        embeddings = self._generate_embeddings(texts)
        
        # Add embeddings to FAISS index
        document_ids = list(range(len(self.document_metadata), 
                                len(self.document_metadata) + len(documents)))
        
        # Convert embeddings to the format FAISS expects
        faiss_embeddings = np.array(embeddings).astype('float32')
        
        # Add to index
        self.index.add(faiss_embeddings)
        
        # Update metadata
        for i, doc_id in enumerate(document_ids):
            # Store everything except the full content to save space
            metadata = {k: v for k, v in documents[i].items() if k != 'content'}
            # Add a small content preview
            metadata['content_preview'] = documents[i]['content'][:200] + "..." 
            self.document_metadata[str(doc_id)] = metadata
        
        # Save updated index and metadata
        self._save_index()
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of document metadata dictionaries with similarity scores
        """
        if self.index is None or len(self.document_metadata) == 0:
            logger.warning("No documents in vector store")
            return []
        
        # Generate embedding for the query
        query_embedding = self._generate_embeddings([query])[0]
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, limit)
        
        # Convert to list of results
        results = []
        for i, doc_idx in enumerate(indices[0]):
            if doc_idx < 0 or doc_idx >= len(self.document_metadata):
                continue  # Skip invalid indices
                
            doc_id = str(doc_idx)
            if doc_id in self.document_metadata:
                result = self.document_metadata[doc_id].copy()
                # Add similarity score (convert distance to similarity)
                similarity = 1.0 / (1.0 + distances[0][i])
                result['similarity'] = similarity
                results.append(result)
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def remove_document(self, document_path: str) -> bool:
        """
        Remove a document from the vector store
        Note: FAISS doesn't support direct removal, so we rebuild the index
        
        Args:
            document_path: Path of the document to remove
            
        Returns:
            True if document was removed, False otherwise
        """
        if self.index is None:
            return False
            
        # Find documents to keep
        docs_to_keep = []
        paths_to_remove = set([document_path])
        
        for doc_id, metadata in self.document_metadata.items():
            if metadata['path'] not in paths_to_remove:
                docs_to_keep.append((int(doc_id), metadata))
        
        if len(docs_to_keep) == len(self.document_metadata):
            return False  # Document wasn't in the store
            
        # Rebuild index
        self.index = None
        self.document_metadata = {}
        
        if docs_to_keep:
            # Create new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add documents back
            for doc_id, metadata in sorted(docs_to_keep, key=lambda x: x[0]):
                self.document_metadata[str(doc_id)] = metadata
            
            # Save updated index and metadata
            self._save_index()
        
        return True
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        return self.model.encode(texts).tolist()
    
    def _save_index(self) -> None:
        """Save the FAISS index and document metadata to disk"""
        if self.index is None:
            return
            
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save document metadata
        with open(self.metadata_path, 'w') as f:
            json.dump(self.document_metadata, f, indent=2)
            
        logger.debug(f"Saved vector store to {self.db_path}")
    
    def _load_index(self) -> None:
        """Load the FAISS index and document metadata from disk"""
        # Load FAISS index if it exists
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                logger.debug(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                self.index = None
        
        # Load document metadata if it exists
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    self.document_metadata = json.load(f)
                logger.debug(f"Loaded metadata for {len(self.document_metadata)} documents")
            except Exception as e:
                logger.error(f"Error loading document metadata: {str(e)}")
                self.document_metadata = {}
