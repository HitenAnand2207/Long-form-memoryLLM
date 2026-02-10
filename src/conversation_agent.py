"""
Conversation Agent
Main orchestrator for long-form memory-enabled conversations
"""

import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from memory_extraction import MemoryExtractor
from memory_storage import MemoryStorage
from memory_retrieval import MemoryRetriever


class ConversationAgent:
    """Main agent handling conversations with long-form memory"""
    
    def __init__(
        self,
        db_path: str = "data/memories.db",
        enable_memory: bool = True,
        verbose: bool = False
    ):
        """
        Initialize conversation agent
        
        Args:
            db_path: Path to memory database
            enable_memory: Whether to enable memory system
            verbose: Print detailed logs
        """
        self.verbose = verbose
        self.enable_memory = enable_memory
        
        if self.enable_memory:
            self.extractor = MemoryExtractor()
            self.storage = MemoryStorage(db_path)
            self.retriever = MemoryRetriever(self.storage)
            
            if self.verbose:
                print("✓ Memory system initialized")
        
        # Session management
        self.sessions = {}  # session_id -> session data
    
    def process_turn(
        self,
        session_id: str,
        user_message: str,
        turn_number: Optional[int] = None,
        retrieve_memories: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single conversation turn
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            turn_number: Turn number (auto-incremented if not provided)
            retrieve_memories: Whether to retrieve and inject memories
            
        Returns:
            Response dictionary with message and metadata
        """
        start_time = time.time()
        
        # Initialize session if needed
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "turn_count": 0,
                "last_active": datetime.utcnow().isoformat()
            }
        
        # Increment turn count
        if turn_number is None:
            self.sessions[session_id]["turn_count"] += 1
            turn_number = self.sessions[session_id]["turn_count"]
        else:
            self.sessions[session_id]["turn_count"] = max(
                self.sessions[session_id]["turn_count"], 
                turn_number
            )
        
        self.sessions[session_id]["last_active"] = datetime.utcnow().isoformat()
        
        # Step 1: Retrieve relevant memories
        relevant_memories = []
        if self.enable_memory and retrieve_memories and turn_number > 1:
            retrieval_start = time.time()
            
            relevant_memories = self.retriever.retrieve_relevant_memories(
                session_id=session_id,
                current_turn=turn_number,
                user_message=user_message,
                max_memories=5
            )
            
            retrieval_time = (time.time() - retrieval_start) * 1000
            
            if self.verbose:
                print(f"✓ Retrieved {len(relevant_memories)} memories in {retrieval_time:.1f}ms")
        
        # Step 2: Format memories for prompt
        memory_context = ""
        if relevant_memories:
            memory_context = self.retriever.format_memories_for_prompt(
                relevant_memories,
                include_metadata=False
            )
        
        # Step 3: Generate response (using simple rule-based for demo)
        # In production, this would call an LLM with memory context injected
        response_start = time.time()
        
        assistant_response = self._generate_response(
            user_message=user_message,
            memory_context=memory_context,
            turn_number=turn_number,
            relevant_memories=relevant_memories
        )
        
        response_time = (time.time() - response_start) * 1000
        
        # Step 4: Extract memories from this turn
        extracted_memories = []
        if self.enable_memory:
            extraction_start = time.time()
            
            raw_memories = self.extractor.extract_memories(
                user_message=user_message,
                assistant_response=assistant_response,
                turn_number=turn_number,
                session_id=session_id
            )
            
            # Filter and deduplicate
            filtered_memories = self.extractor.filter_memories(raw_memories, min_confidence=0.6)
            unique_memories = self.extractor.deduplicate_memories(filtered_memories)
            
            # Store memories
            if unique_memories:
                memory_ids = self.storage.store_memories(unique_memories)
                extracted_memories = [
                    m for m, mid in zip(unique_memories, memory_ids) if mid != -1
                ]
            
            extraction_time = (time.time() - extraction_start) * 1000
            
            if self.verbose:
                print(f"✓ Extracted {len(extracted_memories)} memories in {extraction_time:.1f}ms")
        
        # Calculate total latency
        total_time = (time.time() - start_time) * 1000
        
        # Build response
        response = {
            "session_id": session_id,
            "turn_number": turn_number,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "active_memories": [
                {
                    "memory_id": m.get("id"),
                    "content": m.get("content"),
                    "type": m.get("type"),
                    "origin_turn": m.get("source_turn"),
                    "relevance_score": m.get("relevance_score", 0)
                }
                for m in relevant_memories
            ],
            "extracted_memories": [
                {
                    "content": m.get("content"),
                    "type": m.get("type"),
                    "confidence": m.get("confidence")
                }
                for m in extracted_memories
            ],
            "performance": {
                "total_latency_ms": round(total_time, 2),
                "retrieval_latency_ms": round(retrieval_time, 2) if retrieve_memories else 0,
                "response_latency_ms": round(response_time, 2),
                "extraction_latency_ms": round(extraction_time, 2) if self.enable_memory else 0
            }
        }
        
        return response
    
    def _generate_response(
        self,
        user_message: str,
        memory_context: str,
        turn_number: int,
        relevant_memories: List[Dict[str, Any]]
    ) -> str:
        """
        Generate assistant response
        
        This is a simplified version. In production, this would:
        1. Build a prompt with memory context
        2. Call an LLM (GPT-4, Claude, etc.)
        3. Return the generated response
        """
        # Simple rule-based responses for demo
        message_lower = user_message.lower()
        
        # Check for memory-dependent responses
        if "call" in message_lower and "tomorrow" in message_lower:
            # Look for time constraints in memories
            time_constraints = [
                m for m in relevant_memories 
                if m.get("type") == "constraint" and "time" in m.get("key", "").lower()
            ]
            
            if time_constraints:
                constraint = time_constraints[0]
                return f"I'll make sure to call you tomorrow {constraint.get('value', '')} as you preferred."
            else:
                return "I'll call you tomorrow. What time works best for you?"
        
        elif "language" in message_lower or "preferred language" in message_lower:
            return "I'll remember your language preference for our future conversations."
        
        elif "my name is" in message_lower or "call me" in message_lower:
            return "Got it! I'll remember that."
        
        elif any(word in message_lower for word in ["hello", "hi", "hey"]):
            # Check for name preference
            name_prefs = [
                m for m in relevant_memories 
                if m.get("type") == "preference" and m.get("key") == "name"
            ]
            
            if name_prefs:
                name = name_prefs[0].get("value", "")
                return f"Hello {name}! How can I help you today?"
            else:
                return "Hello! How can I help you today?"
        
        else:
            # Default response with memory awareness
            if memory_context:
                return f"I understand. Based on what I remember about you, I'll keep that in mind. How else can I assist you?"
            else:
                return "I understand. How can I help you with that?"
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session and its memories"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session_data = self.sessions[session_id]
        
        summary = {
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "last_active": session_data["last_active"],
            "total_turns": session_data["turn_count"]
        }
        
        if self.enable_memory:
            # Get memory statistics
            memory_stats = self.storage.get_memory_stats(session_id)
            retrieval_stats = self.retriever.get_retrieval_stats(session_id)
            
            summary["memory_stats"] = memory_stats
            summary["retrieval_stats"] = retrieval_stats
        
        return summary
    
    def clear_session(self, session_id: str):
        """Clear session and its memories"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if self.enable_memory:
            self.storage.delete_session_memories(session_id)
    
    def close(self):
        """Clean up resources"""
        if self.enable_memory:
            self.storage.close()


# Example usage
if __name__ == "__main__":
    agent = ConversationAgent(verbose=True)
    
    session_id = "demo_session"
    
    # Simulate a multi-turn conversation
    turns = [
        "My preferred language is Kannada",
        "Please call me Arun",
        "I'm only available after 11 AM",
        "Hello!",
        "Can you call me tomorrow?"
    ]
    
    print("=" * 60)
    print("DEMO: Long-Form Memory Conversation")
    print("=" * 60)
    
    for i, user_msg in enumerate(turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_msg}")
        
        response = agent.process_turn(
            session_id=session_id,
            user_message=user_msg,
            turn_number=i
        )
        
        print(f"Assistant: {response['assistant_response']}")
        
        if response.get('extracted_memories'):
            print(f"\nExtracted {len(response['extracted_memories'])} new memories")
        
        if response.get('active_memories'):
            print(f"Using {len(response['active_memories'])} active memories:")
            for mem in response['active_memories']:
                print(f"  - {mem['content']} (from turn {mem['origin_turn']})")
        
        print(f"Latency: {response['performance']['total_latency_ms']:.1f}ms")
    
    print("\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    
    summary = agent.get_session_summary(session_id)
    print(json.dumps(summary, indent=2))
    
    agent.close()