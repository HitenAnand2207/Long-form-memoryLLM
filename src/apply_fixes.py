#!/usr/bin/env python3
"""
Apply All Bug Fixes Script
Run this to fix all known bugs in one go
"""

import os
import sys

def print_status(message, status="info"):
    """Print colored status message"""
    colors = {
        "info": "\033[94m",  # Blue
        "success": "\033[92m",  # Green
        "error": "\033[91m",  # Red
        "warning": "\033[93m"  # Yellow
    }
    reset = "\033[0m"
    
    symbols = {
        "info": "ℹ",
        "success": "✓",
        "error": "✗",
        "warning": "⚠"
    }
    
    color = colors.get(status, "")
    symbol = symbols.get(status, "•")
    
    print(f"{color}{symbol} {message}{reset}")


def fix_memory_storage():
    """Fix VECTOR_SEARCH_AVAILABLE scoping issue"""
    filepath = "src/memory_storage.py"
    
    if not os.path.exists(filepath):
        print_status(f"{filepath} not found!", "error")
        return False
    
    print_status(f"Fixing {filepath}...", "info")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already fixed
    if "global VECTOR_SEARCH_AVAILABLE" in content:
        print_status(f"{filepath} already fixed", "success")
        return True
    
    # Apply fix
    old_code = """try:
    import faiss
    from sentence_transformers import SentenceTransformer
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    print("Warning: FAISS or sentence-transformers not available. Vector search disabled.")


class MemoryStorage:
    \"\"\"Hybrid storage system using SQLite and FAISS\"\"\"
    
    def __init__(self, db_path: str = "data/memories.db", embedding_model: str = "all-MiniLM-L6-v2"):
        \"\"\"
        Initialize storage system
        
        Args:
            db_path: Path to SQLite database
            embedding_model: Sentence transformer model for embeddings
        \"\"\"
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
        
        self.vector_search_enabled = VECTOR_SEARCH_AVAILABLE"""
    
    new_code = """# Global flag for vector search availability
VECTOR_SEARCH_AVAILABLE = False

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    print("Warning: FAISS or sentence-transformers not available. Vector search disabled.")
    print("The system will work with text-based search fallback.")


class MemoryStorage:
    \"\"\"Hybrid storage system using SQLite and FAISS\"\"\"
    
    def __init__(self, db_path: str = "data/memories.db", embedding_model: str = "all-MiniLM-L6-v2"):
        \"\"\"
        Initialize storage system
        
        Args:
            db_path: Path to SQLite database
            embedding_model: Sentence transformer model for embeddings
        \"\"\"
        global VECTOR_SEARCH_AVAILABLE
        
        self.db_path = db_path
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self.vector_search_enabled = False
        
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
                self.vector_search_enabled = True
            except Exception as e:
                print(f"Warning: Could not initialize vector search: {e}")
                print("Falling back to text-based search.")
                self.vector_search_enabled = False"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_status(f"{filepath} fixed successfully", "success")
        return True
    else:
        print_status(f"{filepath} - fix pattern not found (may be already fixed)", "warning")
        return True


def fix_conversation_agent():
    """Fix retrieval_time and extraction_time initialization"""
    filepath = "src/conversation_agent.py"
    
    if not os.path.exists(filepath):
        print_status(f"{filepath} not found!", "error")
        return False
    
    print_status(f"Fixing {filepath}...", "info")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already fixed
    if "retrieval_time = 0.0  # Initialize variable" in content:
        print_status(f"{filepath} already fixed", "success")
        return True
    
    # Fix retrieval_time
    old_retrieval = """        # Step 1: Retrieve relevant memories
        relevant_memories = []
        if self.enable_memory and retrieve_memories and turn_number > 1:"""
    
    new_retrieval = """        # Step 1: Retrieve relevant memories
        relevant_memories = []
        retrieval_time = 0.0  # Initialize variable
        
        if self.enable_memory and retrieve_memories and turn_number > 1:"""
    
    content = content.replace(old_retrieval, new_retrieval)
    
    # Fix extraction_time
    old_extraction = """        # Step 4: Extract memories from this turn
        extracted_memories = []
        if self.enable_memory:"""
    
    new_extraction = """        # Step 4: Extract memories from this turn
        extracted_memories = []
        extraction_time = 0.0  # Initialize variable
        
        if self.enable_memory:"""
    
    content = content.replace(old_extraction, new_extraction)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_status(f"{filepath} fixed successfully", "success")
    return True


def main():
    """Main function to apply all fixes"""
    print("=" * 70)
    print("  Applying All Bug Fixes")
    print("=" * 70)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("src"):
        print_status("Error: src/ directory not found", "error")
        print_status("Please run this script from the project root directory", "error")
        sys.exit(1)
    
    fixes = [
        ("Memory Storage (VECTOR_SEARCH_AVAILABLE)", fix_memory_storage),
        ("Conversation Agent (retrieval_time/extraction_time)", fix_conversation_agent),
    ]
    
    success_count = 0
    total_count = len(fixes)
    
    for name, fix_func in fixes:
        print()
        print(f"Applying fix: {name}")
        print("-" * 70)
        
        try:
            if fix_func():
                success_count += 1
        except Exception as e:
            print_status(f"Error applying fix: {e}", "error")
    
    print()
    print("=" * 70)
    print(f"  Fixes Applied: {success_count}/{total_count}")
    print("=" * 70)
    print()
    
    if success_count == total_count:
        print_status("All fixes applied successfully! ✨", "success")
        print()
        print("You can now run:")
        print("  python src/demo.py")
        print("  python run_demo.py")
        print()
    else:
        print_status(f"Some fixes failed ({total_count - success_count})", "warning")
        print()
        print("Please check the error messages above")
        print("You may need to apply fixes manually")
        print()
    
    return success_count == total_count


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print_status("Fix process interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        print()
        print_status(f"Unexpected error: {e}", "error")
        sys.exit(1)