"""
Memory Storage Module
Handles persistence of memories using SQLite and FAISS vector database
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import pickle

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    print("Warning: FAISS or sentence-transformers not available. Vector search disabled.")


class MemoryStorage:
    """Hybrid storage system using SQLite and FAISS"""
    
    def __init__(self, db_path: str = "data/memories.db", embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize storage system
        
        Args:
            db_path: Path to SQLite database
            embedding_model: Sentence transformer model for embeddings
        """
        self.db_path = db_path
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else "data", exist_ok=True)
        
        # Initialize SQLite database
        self._init_database()
        
        # Initialize vector search if available
        if VECTOR_SEARCH_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(embedding_model)
                self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
                self.index = self._load_or_create_index()
                self.memory_id_map = self._load_or_create_id_map()
            except Exception as e:
                print(f"Warning: Could not initialize vector search: {e}")
                VECTOR_SEARCH_AVAILABLE = False
        
        self.vector_search_enabled = VECTOR_SEARCH_AVAILABLE
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                key TEXT,
                value TEXT,
                confidence REAL,
                source_turn INTEGER,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                raw_text TEXT,
                embedding_id INTEGER,
                UNIQUE(session_id, type, key, value, source_turn)
            )
        """)
        
        # Create indices for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON memories(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_turn ON memories(source_turn)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_type ON memories(session_id, type)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        index_path = "data/embeddings/faiss.index"
        
        if os.path.exists(index_path):
            try:
                index = faiss.read_index(index_path)
                return index
            except:
                pass
        
        # Create new index
        os.makedirs("data/embeddings", exist_ok=True)
        index = faiss.IndexFlatL2(self.embedding_dim)
        return index
    
    def _load_or_create_id_map(self):
        """Load or create mapping between FAISS index positions and memory IDs"""
        map_path = "data/embeddings/id_map.pkl"
        
        if os.path.exists(map_path):
            try:
                with open(map_path, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        return []
    
    def _save_index(self):
        """Save FAISS index and ID mapping"""
        if not self.vector_search_enabled:
            return
        
        os.makedirs("data/embeddings", exist_ok=True)
        faiss.write_index(self.index, "data/embeddings/faiss.index")
        
        with open("data/embeddings/id_map.pkl", 'wb') as f:
            pickle.dump(self.memory_id_map, f)
    
    def store_memory(self, memory: Dict[str, Any]) -> int:
        """
        Store a single memory
        
        Args:
            memory: Memory dictionary
            
        Returns:
            Memory ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO memories 
                (session_id, type, content, key, value, confidence, source_turn, 
                 created_at, last_accessed, access_count, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.get("session_id"),
                memory.get("type"),
                memory.get("content"),
                memory.get("key"),
                memory.get("value"),
                memory.get("confidence"),
                memory.get("source_turn"),
                memory.get("created_at"),
                memory.get("last_accessed"),
                memory.get("access_count", 0),
                memory.get("raw_text")
            ))
            
            memory_id = cursor.lastrowid
            
            # Add to vector index if enabled
            if self.vector_search_enabled:
                self._add_to_vector_index(memory_id, memory.get("content"))
            
            conn.commit()
            return memory_id
            
        except sqlite3.IntegrityError:
            # Memory already exists
            return -1
        finally:
            conn.close()
    
    def store_memories(self, memories: List[Dict[str, Any]]) -> List[int]:
        """Store multiple memories"""
        memory_ids = []
        for memory in memories:
            memory_id = self.store_memory(memory)
            if memory_id != -1:
                memory_ids.append(memory_id)
        return memory_ids
    
    def _add_to_vector_index(self, memory_id: int, content: str):
        """Add memory to FAISS vector index"""
        if not self.vector_search_enabled:
            return
        
        # Generate embedding
        embedding = self.encoder.encode([content])[0]
        embedding = np.array([embedding], dtype=np.float32)
        
        # Add to index
        self.index.add(embedding)
        self.memory_id_map.append(memory_id)
        
        # Save periodically (every 10 memories)
        if len(self.memory_id_map) % 10 == 0:
            self._save_index()
    
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_session_memories(
        self, 
        session_id: str, 
        memory_type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Retrieve all memories for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE session_id = ? AND type = ? AND confidence >= ?
                ORDER BY source_turn
            """, (session_id, memory_type, min_confidence))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE session_id = ? AND confidence >= ?
                ORDER BY source_turn
            """, (session_id, min_confidence))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_memories_by_content(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories using vector similarity
        
        Args:
            query: Search query
            session_id: Optional session filter
            top_k: Number of results to return
            
        Returns:
            List of relevant memories
        """
        if not self.vector_search_enabled:
            # Fallback to simple text search
            return self._text_search(query, session_id, top_k)
        
        # Generate query embedding
        query_embedding = self.encoder.encode([query])[0]
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k * 2, len(self.memory_id_map)))
        
        # Retrieve memories
        memories = []
        for idx in indices[0]:
            if idx < len(self.memory_id_map):
                memory_id = self.memory_id_map[idx]
                memory = self.get_memory(memory_id)
                
                if memory:
                    # Filter by session if specified
                    if session_id is None or memory.get("session_id") == session_id:
                        memories.append(memory)
                        
                        if len(memories) >= top_k:
                            break
        
        return memories
    
    def _text_search(self, query: str, session_id: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """Fallback text search using SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_pattern = f"%{query}%"
        
        if session_id:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE session_id = ? AND (content LIKE ? OR value LIKE ?)
                ORDER BY confidence DESC
                LIMIT ?
            """, (session_id, query_pattern, query_pattern, top_k))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE content LIKE ? OR value LIKE ?
                ORDER BY confidence DESC
                LIMIT ?
            """, (query_pattern, query_pattern, top_k))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def update_memory_access(self, memory_id: int):
        """Update last accessed time and increment access count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE memories 
            SET last_accessed = ?, access_count = access_count + 1
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), memory_id))
        
        conn.commit()
        conn.close()
    
    def delete_session_memories(self, session_id: str):
        """Delete all memories for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        # Note: This doesn't remove from FAISS index (would require rebuild)
        # For production, implement periodic index rebuilding
    
    def get_memory_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    MIN(source_turn) as earliest_turn,
                    MAX(source_turn) as latest_turn
                FROM memories
                WHERE session_id = ?
            """, (session_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    MIN(source_turn) as earliest_turn,
                    MAX(source_turn) as latest_turn
                FROM memories
            """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_memories": row[0],
            "avg_confidence": row[1],
            "earliest_turn": row[2],
            "latest_turn": row[3]
        }
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary"""
        return {
            "id": row[0],
            "session_id": row[1],
            "type": row[2],
            "content": row[3],
            "key": row[4],
            "value": row[5],
            "confidence": row[6],
            "source_turn": row[7],
            "created_at": row[8],
            "last_accessed": row[9],
            "access_count": row[10],
            "raw_text": row[11]
        }
    
    def close(self):
        """Clean up resources"""
        if self.vector_search_enabled:
            self._save_index()


# Example usage
if __name__ == "__main__":
    storage = MemoryStorage()
    
    # Test storage
    test_memory = {
        "session_id": "test_session",
        "type": "preference",
        "content": "preferred language is Kannada",
        "key": "language",
        "value": "Kannada",
        "confidence": 0.95,
        "source_turn": 1,
        "created_at": datetime.utcnow().isoformat(),
        "last_accessed": None,
        "access_count": 0,
        "raw_text": "My preferred language is Kannada"
    }
    
    memory_id = storage.store_memory(test_memory)
    print(f"Stored memory with ID: {memory_id}")
    
    # Retrieve
    retrieved = storage.get_memory(memory_id)
    print(f"Retrieved: {json.dumps(retrieved, indent=2)}")
    
    # Search
    results = storage.search_memories_by_content("language", session_id="test_session")
    print(f"Search results: {len(results)}")
    
    storage.close()