"""
Unit Tests for Long-Form Memory System
"""

import pytest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_extraction import MemoryExtractor, MemoryType
from memory_storage import MemoryStorage
from memory_retrieval import MemoryRetriever
from conversation_agent import ConversationAgent


class TestMemoryExtraction:
    """Test memory extraction functionality"""
    
    def setup_method(self):
        self.extractor = MemoryExtractor()
    
    def test_extract_preference(self):
        """Test preference extraction"""
        message = "My preferred language is Kannada"
        memories = self.extractor.extract_memories(
            user_message=message,
            assistant_response="Got it!",
            turn_number=1,
            session_id="test"
        )
        
        # Should extract at least one preference
        prefs = [m for m in memories if m['type'] == MemoryType.PREFERENCE.value]
        assert len(prefs) > 0
        assert any('kannada' in m['content'].lower() for m in prefs)
    
    def test_extract_constraint(self):
        """Test constraint extraction"""
        message = "Please call me only after 11 AM"
        memories = self.extractor.extract_memories(
            user_message=message,
            assistant_response="I'll remember that",
            turn_number=1,
            session_id="test"
        )
        
        constraints = [m for m in memories if m['type'] == MemoryType.CONSTRAINT.value]
        assert len(constraints) > 0
        assert any('11' in m['content'] for m in constraints)
    
    def test_extract_commitment(self):
        """Test commitment extraction"""
        message = "Can you call me tomorrow?"
        memories = self.extractor.extract_memories(
            user_message=message,
            assistant_response="Sure",
            turn_number=1,
            session_id="test"
        )
        
        commitments = [m for m in memories if m['type'] == MemoryType.COMMITMENT.value]
        assert len(commitments) > 0
    
    def test_confidence_scoring(self):
        """Test that confidence scores are reasonable"""
        message = "My preferred language is Kannada"
        memories = self.extractor.extract_memories(
            user_message=message,
            assistant_response="Got it!",
            turn_number=1,
            session_id="test"
        )
        
        for memory in memories:
            assert 0.0 <= memory['confidence'] <= 1.0
    
    def test_filter_low_confidence(self):
        """Test filtering by confidence threshold"""
        memories = [
            {'confidence': 0.9, 'content': 'high'},
            {'confidence': 0.5, 'content': 'medium'},
            {'confidence': 0.3, 'content': 'low'}
        ]
        
        filtered = self.extractor.filter_memories(memories, min_confidence=0.6)
        assert len(filtered) == 1
        assert filtered[0]['content'] == 'high'
    
    def test_deduplication(self):
        """Test memory deduplication"""
        memories = [
            {'type': 'preference', 'key': 'language', 'value': 'Kannada'},
            {'type': 'preference', 'key': 'language', 'value': 'Kannada'},  # Duplicate
            {'type': 'preference', 'key': 'name', 'value': 'John'}
        ]
        
        unique = self.extractor.deduplicate_memories(memories)
        assert len(unique) == 2


class TestMemoryStorage:
    """Test memory storage functionality"""
    
    def setup_method(self):
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memories.db")
        self.storage = MemoryStorage(db_path=self.db_path)
    
    def teardown_method(self):
        self.storage.close()
        shutil.rmtree(self.temp_dir)
    
    def test_store_and_retrieve_memory(self):
        """Test basic storage and retrieval"""
        memory = {
            "session_id": "test_session",
            "type": "preference",
            "content": "language is Kannada",
            "key": "language",
            "value": "Kannada",
            "confidence": 0.95,
            "source_turn": 1,
            "created_at": "2024-01-01T00:00:00",
            "last_accessed": None,
            "access_count": 0,
            "raw_text": "My language is Kannada"
        }
        
        memory_id = self.storage.store_memory(memory)
        assert memory_id > 0
        
        retrieved = self.storage.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved['content'] == memory['content']
    
    def test_get_session_memories(self):
        """Test retrieving all memories for a session"""
        session_id = "test_session"
        
        # Store multiple memories
        for i in range(3):
            memory = {
                "session_id": session_id,
                "type": "fact",
                "content": f"fact {i}",
                "key": "test",
                "value": f"value {i}",
                "confidence": 0.8,
                "source_turn": i,
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": None,
                "access_count": 0,
                "raw_text": f"test {i}"
            }
            self.storage.store_memory(memory)
        
        memories = self.storage.get_session_memories(session_id)
        assert len(memories) == 3
    
    def test_filter_by_type(self):
        """Test filtering memories by type"""
        session_id = "test_session"
        
        # Store different types
        types = ["preference", "fact", "constraint"]
        for mem_type in types:
            memory = {
                "session_id": session_id,
                "type": mem_type,
                "content": f"test {mem_type}",
                "key": "test",
                "value": "test",
                "confidence": 0.8,
                "source_turn": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": None,
                "access_count": 0,
                "raw_text": "test"
            }
            self.storage.store_memory(memory)
        
        prefs = self.storage.get_session_memories(session_id, memory_type="preference")
        assert len(prefs) == 1
        assert prefs[0]['type'] == "preference"
    
    def test_update_access(self):
        """Test updating memory access statistics"""
        memory = {
            "session_id": "test_session",
            "type": "fact",
            "content": "test",
            "key": "test",
            "value": "test",
            "confidence": 0.8,
            "source_turn": 1,
            "created_at": "2024-01-01T00:00:00",
            "last_accessed": None,
            "access_count": 0,
            "raw_text": "test"
        }
        
        memory_id = self.storage.store_memory(memory)
        
        # Update access
        self.storage.update_memory_access(memory_id)
        
        retrieved = self.storage.get_memory(memory_id)
        assert retrieved['access_count'] == 1
        assert retrieved['last_accessed'] is not None


class TestMemoryRetrieval:
    """Test memory retrieval functionality"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memories.db")
        self.storage = MemoryStorage(db_path=self.db_path)
        self.retriever = MemoryRetriever(self.storage)
    
    def teardown_method(self):
        self.storage.close()
        shutil.rmtree(self.temp_dir)
    
    def test_retrieve_relevant_memories(self):
        """Test relevance-based retrieval"""
        session_id = "test_session"
        
        # Store memories at different turns
        memories = [
            {
                "session_id": session_id,
                "type": "preference",
                "content": "language is Kannada",
                "key": "language",
                "value": "Kannada",
                "confidence": 0.95,
                "source_turn": 1,
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": None,
                "access_count": 0,
                "raw_text": "My language is Kannada"
            },
            {
                "session_id": session_id,
                "type": "constraint",
                "content": "call after 11 AM",
                "key": "time_constraint",
                "value": "after 11 AM",
                "confidence": 0.9,
                "source_turn": 5,
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": None,
                "access_count": 0,
                "raw_text": "Please call after 11 AM"
            }
        ]
        
        for memory in memories:
            self.storage.store_memory(memory)
        
        # Retrieve memories relevant to "call"
        relevant = self.retriever.retrieve_relevant_memories(
            session_id=session_id,
            current_turn=100,
            user_message="Can you call me?",
            max_memories=5
        )
        
        assert len(relevant) > 0
        # Should retrieve the time constraint as it's relevant to calling
        assert any('call' in m['content'].lower() for m in relevant)
    
    def test_recency_weighting(self):
        """Test that recent memories get higher relevance"""
        session_id = "test_session"
        
        # Store same type of memory at different turns
        for turn in [1, 50, 100]:
            memory = {
                "session_id": session_id,
                "type": "fact",
                "content": f"test fact from turn {turn}",
                "key": "test",
                "value": f"turn {turn}",
                "confidence": 0.8,
                "source_turn": turn,
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": None,
                "access_count": 0,
                "raw_text": f"test {turn}"
            }
            self.storage.store_memory(memory)
        
        relevant = self.retriever.retrieve_relevant_memories(
            session_id=session_id,
            current_turn=105,
            user_message="test",
            max_memories=3
        )
        
        # More recent memory should have higher relevance
        if len(relevant) >= 2:
            assert relevant[0]['source_turn'] >= relevant[-1]['source_turn']


class TestConversationAgent:
    """Test end-to-end conversation agent"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memories.db")
        self.agent = ConversationAgent(db_path=self.db_path, verbose=False)
    
    def teardown_method(self):
        self.agent.close()
        shutil.rmtree(self.temp_dir)
    
    def test_process_turn(self):
        """Test processing a conversation turn"""
        response = self.agent.process_turn(
            session_id="test_session",
            user_message="My preferred language is Kannada",
            turn_number=1
        )
        
        assert 'assistant_response' in response
        assert 'extracted_memories' in response
        assert len(response['extracted_memories']) > 0
    
    def test_long_range_memory(self):
        """Test memory retention across many turns"""
        session_id = "test_session"
        
        # Turn 1: Set preference
        response1 = self.agent.process_turn(
            session_id=session_id,
            user_message="My preferred language is Kannada",
            turn_number=1
        )
        
        assert len(response1['extracted_memories']) > 0
        
        # Turn 100: Should recall preference
        response100 = self.agent.process_turn(
            session_id=session_id,
            user_message="What language do I prefer?",
            turn_number=100
        )
        
        # Should have active memories
        assert len(response100.get('active_memories', [])) > 0
    
    def test_performance_metrics(self):
        """Test that performance metrics are tracked"""
        response = self.agent.process_turn(
            session_id="test_session",
            user_message="Test message",
            turn_number=1
        )
        
        assert 'performance' in response
        assert 'total_latency_ms' in response['performance']
        assert response['performance']['total_latency_ms'] > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])