"""
Diagnostic and Fix Script for Long-Form Memory System
Run this if you encounter any issues
"""

import sys
import os

print("=" * 70)
print("  DIAGNOSTIC SCRIPT - Long-Form Memory System")
print("=" * 70)
print()

# Check Python version
print("1. Checking Python version...")
python_version = sys.version_info
print(f"   Python {python_version.major}.{python_version.minor}.{python_version.micro}")
if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
    print("   ⚠️  WARNING: Python 3.9+ recommended")
else:
    print("   ✓ Python version OK")
print()

# Check required packages
print("2. Checking required packages...")
required_packages = {
    'flask': 'Flask',
    'sqlalchemy': 'SQLAlchemy',
}

optional_packages = {
    'faiss': 'FAISS (for vector search)',
    'sentence_transformers': 'Sentence Transformers (for embeddings)',
}

missing_required = []
missing_optional = []

for package, name in required_packages.items():
    try:
        __import__(package)
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ✗ {name} - MISSING (REQUIRED)")
        missing_required.append(package)

for package, name in optional_packages.items():
    try:
        __import__(package)
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ⚠️  {name} - MISSING (Optional - will use fallback)")
        missing_optional.append(package)

print()

# Check data directory
print("3. Checking data directory...")
if os.path.exists("data"):
    print("   ✓ Data directory exists")
else:
    print("   Creating data directory...")
    os.makedirs("data/embeddings", exist_ok=True)
    print("   ✓ Data directory created")
print()

# Fix suggestions
if missing_required:
    print("⚠️  REQUIRED PACKAGES MISSING!")
    print()
    print("Run this command to install missing packages:")
    print(f"   pip install {' '.join(missing_required)}")
    print()

if missing_optional:
    print("ℹ️  Optional packages missing (system will work without them):")
    print()
    print("To enable full features, run:")
    print(f"   pip install {' '.join(missing_optional)}")
    print()
    print("Note: FAISS and sentence-transformers are optional.")
    print("The system will use text-based search if they're not available.")
    print()

# Test basic imports
print("4. Testing core modules...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from memory_extraction import MemoryExtractor
    print("   ✓ Memory extraction module")
except Exception as e:
    print(f"   ✗ Memory extraction module: {e}")

try:
    from memory_storage import MemoryStorage
    print("   ✓ Memory storage module")
except Exception as e:
    print(f"   ✗ Memory storage module: {e}")

try:
    from memory_retrieval import MemoryRetriever
    print("   ✓ Memory retrieval module")
except Exception as e:
    print(f"   ✗ Memory retrieval module: {e}")

try:
    from conversation_agent import ConversationAgent
    print("   ✓ Conversation agent module")
except Exception as e:
    print(f"   ✗ Conversation agent module: {e}")

print()

# Summary
print("=" * 70)
print("  DIAGNOSTIC COMPLETE")
print("=" * 70)
print()

if missing_required:
    print("⚠️  ACTION REQUIRED: Install missing required packages")
    print(f"   pip install {' '.join(missing_required)}")
else:
    print("✓ All required packages installed!")
    print()
    print("You can now run:")
    print("   python src/demo.py")
    print()
    
if missing_optional:
    print("💡 TIP: For best performance, install optional packages:")
    print(f"   pip install {' '.join(missing_optional)}")
    print()
    print("   Without FAISS/sentence-transformers:")
    print("   - System will use text-based search (still works well)")
    print("   - Slightly lower relevance in memory retrieval")
    print()