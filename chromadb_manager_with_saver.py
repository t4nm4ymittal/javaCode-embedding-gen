import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import chromadb
from sentence_transformers import SentenceTransformer


@dataclass
class CodeChunk:
    content: str
    start_line: int
    end_line: int
    chunk_type: str
    metadata: Dict


class ChromaDBManagerWithEmbeddingSaver:
    """
    Enhanced ChromaDB manager that saves embeddings to disk.
    
    Features:
    - Generates embeddings explicitly
    - Saves embeddings + text to disk
    - Separate directories for document embeddings and query embeddings
    - JSON format for easy inspection
    - Caching support
    """
    
    def __init__(
        self,
        collection_name: str = "java_code",
        persist_directory: str = "./chroma_db",
        embedding_directory: str = "./embeddings",
        model_name: str = "all-MiniLM-L6-v2",
        save_embeddings: bool = True
    ):
        """
        Initialize ChromaDB manager with embedding saving.
        
        Args:
            collection_name: Name of the collection to store chunks
            persist_directory: Directory where ChromaDB stores data
            embedding_directory: Directory to save embeddings and text
            model_name: Sentence transformer model name
            save_embeddings: Whether to save embeddings to disk
        """
        self.save_embeddings = save_embeddings
        
        # Setup embedding directories
        self.embedding_dir = Path(embedding_directory)
        self.documents_dir = self.embedding_dir / "documents"
        self.queries_dir = self.embedding_dir / "queries"
        
        if self.save_embeddings:
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            self.queries_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Embedding directories created:")
            print(f"   Documents: {self.documents_dir}")
            print(f"   Queries: {self.queries_dir}")
        
        # Load embedding model
        print(f"\n🔧 Loading embedding model '{model_name}'...")
        self.embedding_model = SentenceTransformer(model_name)
        print(f"  ✓ Model loaded")
        print(f"  • Dimensions: {self.embedding_model.get_sentence_embedding_dimension()}")
        print(f"  • Max sequence length: {self.embedding_model.max_seq_length}")

        # Create ChromaDB client
        print(f"\n💾 Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Java code chunks with semantic embeddings"}
        )
        
        print(f"  ✓ ChromaDB initialized")
        print(f"  • Collection: {collection_name}")
        print(f"  • Storage: {persist_directory}")
        print(f"  • Existing chunks: {self.collection.count()}")
        
        # Statistics
        self.stats = {
            "documents_embedded": 0,
            "queries_embedded": 0,
            "total_embeddings_generated": 0
        }
    
    def generate_embedding(self, text: str, is_query: bool = False) -> np.ndarray:
        """
        Generate embedding for text and optionally save to disk.
        
        Args:
            text: Text to embed
            is_query: Whether this is a query (vs document)
            
        Returns:
            numpy array of embedding
        """
        # Generate embedding
        embedding = self.embedding_model.encode(text, show_progress_bar=False)
        
        # Update statistics
        self.stats["total_embeddings_generated"] += 1
        if is_query:
            self.stats["queries_embedded"] += 1
        else:
            self.stats["documents_embedded"] += 1
        
        # Save to disk if enabled
        if self.save_embeddings:
            self._save_embedding_to_disk(text, embedding, is_query)
        
        return embedding
    
    def _save_embedding_to_disk(self, text: str, embedding: np.ndarray, is_query: bool):
        """
        Save embedding and associated text to disk.
        
        File format:
        {
            "text": "original text",
            "embedding": [0.123, -0.456, ...],
            "metadata": {
                "timestamp": "2024-01-31T10:30:00",
                "type": "query" or "document",
                "dimensions": 384,
                "norm": 12.34,
                "model": "all-MiniLM-L6-v2"
            }
        }
        """
        # Choose directory
        save_dir = self.queries_dir if is_query else self.documents_dir
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        prefix = "query" if is_query else "doc"
        
        # Create safe filename from text
        safe_text = "".join(c if c.isalnum() else "_" for c in text[:50])
        filename = f"{prefix}_{timestamp}_{safe_text}.json"
        filepath = save_dir / filename
        
        # Prepare data
        data = {
            "text": text,
            "embedding": embedding.tolist(),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "type": "query" if is_query else "document",
                "dimensions": len(embedding),
                "norm": float(np.linalg.norm(embedding)),
                "model": self.embedding_model._model_card_vars.get("model_name", "unknown"),
                "text_length": len(text),
                "word_count": len(text.split())
            }
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def add_chunks(self, chunks: List[CodeChunk], batch_size: int = 100):
        """
        Add code chunks to ChromaDB with explicit embedding generation.
        
        Process:
        1. Extract text content from chunks
        2. Generate embeddings explicitly (and save to disk)
        3. Prepare metadata
        4. Add to ChromaDB with pre-computed embeddings
        """
        if not chunks:
            print("No chunks to add")
            return
        
        print(f"\n{'='*70}")
        print(f"🔄 PROCESSING {len(chunks)} CHUNKS")
        print(f"{'='*70}\n")
        
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks, 1):
            # Extract content
            content = chunk.content
            documents.append(content)
            
            # Generate embedding explicitly
            print(f"Chunk {i}/{len(chunks)}:")
            print(f"  Type: {chunk.chunk_type}")
            print(f"  Text length: {len(content)} chars")
            print(f"  Generating embedding...")
            
            embedding = self.generate_embedding(content, is_query=False)
            embeddings.append(embedding.tolist())
            
            print(f"  ✓ Embedding: {len(embedding)} dimensions")
            print(f"    First 5 values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
            print(f"    Norm: {np.linalg.norm(embedding):.4f}")
            
            if self.save_embeddings:
                print(f"    💾 Saved to: {self.documents_dir}")
            print()
            
            # Prepare metadata
            metadata = {
                'chunk_type': chunk.chunk_type,
                'start_line': str(chunk.start_line),
                'end_line': str(chunk.end_line),
                'file_path': chunk.metadata.get('file_path', ''),
                'class_name': chunk.metadata.get('class_name', ''),
                'method_name': chunk.metadata.get('method_name', '')
            }
            metadatas.append(metadata)
            
            # Generate unique ID
            chunk_id = f"{chunk.metadata.get('file_path', 'unknown')}_{chunk.chunk_type}_{i}"
            ids.append(chunk_id)
        
        # Add to ChromaDB in batches
        print(f"{'─'*70}")
        print(f"💾 Storing in ChromaDB...")
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_embeds = embeddings[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                embeddings=batch_embeds,
                metadatas=batch_metas,
                ids=batch_ids
            )
            
            print(f"  Batch {i//batch_size + 1}: Added {len(batch_docs)} chunks")
        
        print(f"\n✓ Successfully added {len(chunks)} chunks to ChromaDB")
        print(f"  Total chunks in collection: {self.collection.count()}")
        self._print_statistics()
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        """
        Search for similar code chunks using semantic similarity.
        Generates query embedding explicitly and saves to disk.
        
        Args:
            query: Search query (e.g., "method to add user")
            n_results: Number of results to return
            
        Returns:
            Dictionary with documents, metadatas, and distances
        """
        print(f"\n{'='*70}")
        print(f"🔍 SEARCH QUERY")
        print(f"{'='*70}")
        print(f"Query: '{query}'")
        print(f"Query length: {len(query)} chars\n")
        
        # Generate query embedding
        print(f"Generating query embedding...")
        query_embedding = self.generate_embedding(query, is_query=True)
        
        print(f"✓ Query embedding: {len(query_embedding)} dimensions")
        print(f"  First 5 values: [{query_embedding[0]:.4f}, {query_embedding[1]:.4f}, {query_embedding[2]:.4f}, ...]")
        print(f"  Norm: {np.linalg.norm(query_embedding):.4f}")
        
        if self.save_embeddings:
            print(f"  💾 Saved to: {self.queries_dir}")
        
        # Search ChromaDB
        print(f"\nSearching ChromaDB...")
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        
        # Display results
        print(f"\n{'─'*70}")
        print(f"📊 SEARCH RESULTS (Top {n_results})")
        print(f"{'─'*70}\n")
        
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            similarity = 1 - distance
            print(f"Result #{i}:")
            print(f"  Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
            print(f"  Type: {meta.get('chunk_type', 'unknown')}")
            print(f"  Class: {meta.get('class_name', 'N/A')}")
            print(f"  Method: {meta.get('method_name', 'N/A')}")
            print(f"  Preview: {doc[:80]}...")
            print()
        
        self._print_statistics()
        return results
    
    def load_embedding_from_disk(self, filepath: str) -> Dict:
        """
        Load a saved embedding from disk.
        
        Returns:
            Dictionary with text, embedding, and metadata
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert embedding back to numpy array
        data['embedding'] = np.array(data['embedding'])
        return data
    
    def list_saved_embeddings(self, embedding_type: str = "all") -> List[Path]:
        """
        List all saved embeddings.
        
        Args:
            embedding_type: "documents", "queries", or "all"
            
        Returns:
            List of file paths
        """
        embeddings = []
        
        if embedding_type in ["documents", "all"]:
            embeddings.extend(self.documents_dir.glob("*.json"))
        
        if embedding_type in ["queries", "all"]:
            embeddings.extend(self.queries_dir.glob("*.json"))
        
        return sorted(embeddings)
    
    def compare_saved_embeddings(self, filepath1: str, filepath2: str):
        """
        Compare two saved embeddings.
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Load embeddings
        data1 = self.load_embedding_from_disk(filepath1)
        data2 = self.load_embedding_from_disk(filepath2)
        
        emb1 = data1['embedding']
        emb2 = data2['embedding']
        
        # Calculate similarity
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        
        print(f"\n{'='*70}")
        print(f"🔬 EMBEDDING COMPARISON")
        print(f"{'='*70}\n")
        print(f"Text 1: {data1['text'][:60]}...")
        print(f"Text 2: {data2['text'][:60]}...\n")
        print(f"Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"Euclidean distance: {np.linalg.norm(emb1 - emb2):.4f}")
        
        return similarity
    
    def get_all_chunks(self) -> Dict:
        """Retrieve all chunks from the collection."""
        return self.collection.get()
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(self.collection.name)
        print(f"✓ Deleted collection: {self.collection.name}")
    
    def clear_saved_embeddings(self, embedding_type: str = "all"):
        """
        Clear saved embeddings from disk.
        
        Args:
            embedding_type: "documents", "queries", or "all"
        """
        count = 0
        
        if embedding_type in ["documents", "all"]:
            for f in self.documents_dir.glob("*.json"):
                f.unlink()
                count += 1
        
        if embedding_type in ["queries", "all"]:
            for f in self.queries_dir.glob("*.json"):
                f.unlink()
                count += 1
        
        print(f"✓ Cleared {count} saved embeddings")
    
    def _print_statistics(self):
        """Print embedding generation statistics."""
        print(f"\n{'─'*70}")
        print(f"📊 STATISTICS")
        print(f"{'─'*70}")
        print(f"Total embeddings generated: {self.stats['total_embeddings_generated']}")
        print(f"  • Documents: {self.stats['documents_embedded']}")
        print(f"  • Queries: {self.stats['queries_embedded']}")
        
        if self.save_embeddings:
            doc_files = len(list(self.documents_dir.glob("*.json")))
            query_files = len(list(self.queries_dir.glob("*.json")))
            print(f"\nSaved to disk:")
            print(f"  • Document embeddings: {doc_files} files")
            print(f"  • Query embeddings: {query_files} files")
            
            # Calculate disk usage
            total_size = sum(f.stat().st_size for f in self.embedding_dir.rglob("*.json"))
            print(f"  • Total disk usage: {total_size / 1024:.2f} KB")
        print(f"{'─'*70}\n")
    
    def export_embeddings_summary(self, output_file: str = "embeddings_summary.json"):
        """
        Export a summary of all embeddings to a JSON file.
        """
        summary = {
            "statistics": self.stats,
            "model_info": {
                "name": self.embedding_model._model_card_vars.get("model_name", "unknown"),
                "dimensions": self.embedding_model.get_sentence_embedding_dimension(),
                "max_seq_length": self.embedding_model.max_seq_length
            },
            "documents": [],
            "queries": []
        }
        
        # Add document embeddings info
        for filepath in self.list_saved_embeddings("documents"):
            data = self.load_embedding_from_disk(str(filepath))
            summary["documents"].append({
                "filename": filepath.name,
                "text_preview": data['text'][:100],
                "metadata": data['metadata']
            })
        
        # Add query embeddings info
        for filepath in self.list_saved_embeddings("queries"):
            data = self.load_embedding_from_disk(str(filepath))
            summary["queries"].append({
                "filename": filepath.name,
                "text": data['text'],
                "metadata": data['metadata']
            })
        
        # Save summary
        output_path = self.embedding_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported summary to: {output_path}")
        return output_path


print("✓ ChromaDBManagerWithEmbeddingSaver class defined")
