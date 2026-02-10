"""
Memory Retrieval Module
Retrieves relevant memories based on context, recency, and importance
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict


class MemoryRetriever:
    """Context-aware memory retrieval with relevance ranking"""
    
    def __init__(self, storage):
        """
        Initialize retriever
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Retrieval parameters
        self.recency_weight = 0.3
        self.confidence_weight = 0.4
        self.access_count_weight = 0.2
        self.semantic_weight = 0.1
        
        # Memory type priorities
        self.type_priorities = {
            "instruction": 1.0,
            "preference": 0.9,
            "commitment": 0.85,
            "constraint": 0.8,
            "fact": 0.7,
            "entity": 0.6
        }
    
    def retrieve_relevant_memories(
        self,
        session_id: str,
        current_turn: int,
        user_message: str,
        max_memories: int = 5,
        min_relevance: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant memories for current context
        
        Args:
            session_id: Current session
            current_turn: Current turn number
            user_message: User's current message
            max_memories: Maximum memories to return
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of relevant memories with relevance scores
        """
        # Get all session memories
        all_memories = self.storage.get_session_memories(session_id)
        
        if not all_memories:
            return []
        
        # Calculate relevance for each memory
        scored_memories = []
        for memory in all_memories:
            relevance_score = self._calculate_relevance(
                memory, 
                current_turn, 
                user_message
            )
            
            if relevance_score >= min_relevance:
                memory_copy = memory.copy()
                memory_copy["relevance_score"] = relevance_score
                scored_memories.append(memory_copy)
        
        # Sort by relevance
        scored_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Apply diversity filtering
        diverse_memories = self._apply_diversity_filter(
            scored_memories, 
            max_memories
        )
        
        # Update access statistics
        for memory in diverse_memories:
            self.storage.update_memory_access(memory["id"])
        
        return diverse_memories[:max_memories]
    
    def _calculate_relevance(
        self, 
        memory: Dict[str, Any], 
        current_turn: int, 
        user_message: str
    ) -> float:
        """
        Calculate relevance score for a memory
        
        Combines multiple signals:
        - Recency (how recent is the memory)
        - Confidence (how confident we are in the memory)
        - Access count (how often has it been used)
        - Semantic similarity (how related to current message)
        - Type priority (importance of memory type)
        """
        # 1. Recency score (exponential decay)
        turn_distance = current_turn - memory.get("source_turn", 0)
        recency_score = math.exp(-turn_distance / 100)  # Decay over ~100 turns
        
        # 2. Confidence score
        confidence_score = memory.get("confidence", 0.5)
        
        # 3. Access count score (logarithmic scaling)
        access_count = memory.get("access_count", 0)
        access_score = math.log(access_count + 1) / math.log(10)  # Normalize to 0-1
        access_score = min(1.0, access_score)
        
        # 4. Semantic similarity score
        semantic_score = self._calculate_semantic_similarity(
            memory.get("content", ""),
            user_message
        )
        
        # 5. Type priority score
        memory_type = memory.get("type", "fact")
        type_score = self.type_priorities.get(memory_type, 0.5)
        
        # Combine scores with weights
        total_score = (
            self.recency_weight * recency_score +
            self.confidence_weight * confidence_score +
            self.access_count_weight * access_score +
            self.semantic_weight * semantic_score
        ) * type_score
        
        return min(1.0, total_score)
    
    def _calculate_semantic_similarity(self, memory_content: str, query: str) -> float:
        """
        Calculate semantic similarity between memory and query
        Uses simple keyword matching (can be enhanced with embeddings)
        """
        # Convert to lowercase and split into words
        memory_words = set(memory_content.lower().split())
        query_words = set(query.lower().split())
        
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are'}
        memory_words -= stopwords
        query_words -= stopwords
        
        if not memory_words or not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(memory_words & query_words)
        union = len(memory_words | query_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _apply_diversity_filter(
        self, 
        memories: List[Dict[str, Any]], 
        max_count: int
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity filtering to avoid redundant memories
        Ensures variety in memory types and content
        """
        if len(memories) <= max_count:
            return memories
        
        diverse_memories = []
        type_counts = defaultdict(int)
        seen_keys = set()
        
        for memory in memories:
            memory_type = memory.get("type")
            memory_key = memory.get("key")
            
            # Prefer diverse types
            if type_counts[memory_type] < 2:  # Max 2 per type
                # Avoid duplicate keys
                if memory_key not in seen_keys or len(diverse_memories) < max_count // 2:
                    diverse_memories.append(memory)
                    type_counts[memory_type] += 1
                    seen_keys.add(memory_key)
                    
                    if len(diverse_memories) >= max_count:
                        break
        
        # Fill remaining slots with highest-scoring memories
        if len(diverse_memories) < max_count:
            for memory in memories:
                if memory not in diverse_memories:
                    diverse_memories.append(memory)
                    if len(diverse_memories) >= max_count:
                        break
        
        return diverse_memories
    
    def retrieve_by_type(
        self,
        session_id: str,
        memory_type: str,
        max_memories: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories of a specific type"""
        memories = self.storage.get_session_memories(
            session_id, 
            memory_type=memory_type
        )
        
        # Sort by confidence and recency
        memories.sort(
            key=lambda x: (x.get("confidence", 0), -x.get("source_turn", 0)),
            reverse=True
        )
        
        return memories[:max_memories]
    
    def retrieve_by_turn_range(
        self,
        session_id: str,
        start_turn: int,
        end_turn: int
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from a specific turn range"""
        all_memories = self.storage.get_session_memories(session_id)
        
        filtered = [
            m for m in all_memories 
            if start_turn <= m.get("source_turn", 0) <= end_turn
        ]
        
        return filtered
    
    def retrieve_critical_memories(
        self,
        session_id: str,
        current_turn: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve critical memories that should always be active
        (instructions, high-priority preferences, commitments)
        """
        critical_types = ["instruction", "commitment"]
        critical_memories = []
        
        for mem_type in critical_types:
            memories = self.retrieve_by_type(session_id, mem_type, max_memories=3)
            critical_memories.extend(memories)
        
        # Also get high-confidence preferences
        preferences = self.retrieve_by_type(session_id, "preference", max_memories=5)
        high_conf_prefs = [p for p in preferences if p.get("confidence", 0) > 0.8]
        critical_memories.extend(high_conf_prefs)
        
        return critical_memories
    
    def format_memories_for_prompt(
        self, 
        memories: List[Dict[str, Any]],
        include_metadata: bool = False
    ) -> str:
        """
        Format memories for injection into LLM prompt
        
        Args:
            memories: List of memory dictionaries
            include_metadata: Whether to include turn numbers and confidence
            
        Returns:
            Formatted string for prompt injection
        """
        if not memories:
            return ""
        
        formatted = ["## Active Memories"]
        
        # Group by type
        by_type = defaultdict(list)
        for memory in memories:
            by_type[memory.get("type", "other")].append(memory)
        
        for mem_type, mems in by_type.items():
            formatted.append(f"\n### {mem_type.title()}s:")
            for mem in mems:
                content = mem.get("content", "")
                
                if include_metadata:
                    turn = mem.get("source_turn", 0)
                    conf = mem.get("confidence", 0)
                    formatted.append(f"- {content} (from turn {turn}, confidence: {conf:.2f})")
                else:
                    formatted.append(f"- {content}")
        
        return "\n".join(formatted)
    
    def get_retrieval_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics about memory retrieval for a session"""
        all_memories = self.storage.get_session_memories(session_id)
        
        if not all_memories:
            return {"total_memories": 0}
        
        # Calculate stats
        total_accesses = sum(m.get("access_count", 0) for m in all_memories)
        avg_confidence = sum(m.get("confidence", 0) for m in all_memories) / len(all_memories)
        
        type_distribution = defaultdict(int)
        for mem in all_memories:
            type_distribution[mem.get("type", "unknown")] += 1
        
        return {
            "total_memories": len(all_memories),
            "total_accesses": total_accesses,
            "avg_confidence": avg_confidence,
            "type_distribution": dict(type_distribution),
            "most_accessed": max(all_memories, key=lambda x: x.get("access_count", 0))
        }


# Example usage
if __name__ == "__main__":
    from memory_storage import MemoryStorage
    
    storage = MemoryStorage()
    retriever = MemoryRetriever(storage)
    
    # Test retrieval
    relevant = retriever.retrieve_relevant_memories(
        session_id="test_session",
        current_turn=100,
        user_message="Can you call me tomorrow?",
        max_memories=5
    )
    
    print(f"Found {len(relevant)} relevant memories")
    for mem in relevant:
        print(f"- {mem['content']} (relevance: {mem.get('relevance_score', 0):.2f})")
    
    # Format for prompt
    formatted = retriever.format_memories_for_prompt(relevant, include_metadata=True)
    print("\nFormatted for prompt:")
    print(formatted)