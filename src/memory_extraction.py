"""
Memory Extraction Module
Identifies and extracts important information from conversation turns
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Types of memories that can be extracted"""
    PREFERENCE = "preference"
    FACT = "fact"
    CONSTRAINT = "constraint"
    COMMITMENT = "commitment"
    INSTRUCTION = "instruction"
    ENTITY = "entity"


class MemoryExtractor:
    """Extracts and classifies important information from conversation turns"""
    
    def __init__(self):
        # Patterns for identifying different memory types
        self.preference_patterns = [
            r"prefer[s]?\s+(.+)",
            r"like[s]?\s+(.+)",
            r"favorite\s+(.+)",
            r"my\s+(.+)\s+is\s+(.+)",
            r"call me\s+(.+)",
            r"language\s+is\s+(\w+)",
        ]
        
        self.constraint_patterns = [
            r"(?:only|must|should|need to)\s+(.+)",
            r"(?:before|after|by)\s+(\d+(?::\d+)?(?:\s*(?:AM|PM|am|pm))?)",
            r"(?:not available|busy|occupied)\s+(.+)",
            r"(?:don't|do not|never)\s+(.+)",
        ]
        
        self.commitment_patterns = [
            r"(?:will|going to|planning to)\s+(.+)",
            r"(?:call|email|text|message|contact)\s+(.+)",
            r"(?:remind me|schedule|set up)\s+(.+)",
            r"(?:tomorrow|next week|later|soon)\s+(.+)?",
        ]
        
        self.instruction_patterns = [
            r"(?:always|never|from now on)\s+(.+)",
            r"(?:remember to|make sure to)\s+(.+)",
            r"(?:whenever|if)\s+(.+)",
        ]
    
    def extract_memories(
        self, 
        user_message: str, 
        assistant_response: str,
        turn_number: int,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract memories from a conversation turn
        
        Args:
            user_message: User's input
            assistant_response: AI's response
            turn_number: Current turn number
            session_id: Session identifier
            
        Returns:
            List of extracted memory objects
        """
        memories = []
        
        # Extract from user message
        memories.extend(self._extract_preferences(user_message, turn_number))
        memories.extend(self._extract_constraints(user_message, turn_number))
        memories.extend(self._extract_commitments(user_message, turn_number))
        memories.extend(self._extract_instructions(user_message, turn_number))
        memories.extend(self._extract_entities(user_message, turn_number))
        memories.extend(self._extract_facts(user_message, turn_number))
        
        # Add metadata to all memories
        for memory in memories:
            memory["session_id"] = session_id
            memory["source_turn"] = turn_number
            memory["created_at"] = datetime.utcnow().isoformat()
            memory["last_accessed"] = None
            memory["access_count"] = 0
        
        return memories
    
    def _extract_preferences(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract user preferences"""
        memories = []
        
        for pattern in self.preference_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0)
                
                # Extract key-value if possible
                key, value = self._parse_preference(content)
                
                memory = {
                    "type": MemoryType.PREFERENCE.value,
                    "content": content,
                    "key": key,
                    "value": value,
                    "confidence": self._calculate_confidence(content, pattern),
                    "raw_text": text
                }
                memories.append(memory)
        
        return memories
    
    def _extract_constraints(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract constraints and limitations"""
        memories = []
        
        for pattern in self.constraint_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0)
                
                memory = {
                    "type": MemoryType.CONSTRAINT.value,
                    "content": content,
                    "key": self._extract_constraint_key(content),
                    "value": match.group(1) if match.groups() else content,
                    "confidence": self._calculate_confidence(content, pattern),
                    "raw_text": text
                }
                memories.append(memory)
        
        return memories
    
    def _extract_commitments(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract commitments and scheduled actions"""
        memories = []
        
        for pattern in self.commitment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0)
                
                memory = {
                    "type": MemoryType.COMMITMENT.value,
                    "content": content,
                    "key": "scheduled_action",
                    "value": match.group(1) if match.groups() else content,
                    "confidence": self._calculate_confidence(content, pattern),
                    "raw_text": text
                }
                memories.append(memory)
        
        return memories
    
    def _extract_instructions(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract long-term instructions"""
        memories = []
        
        for pattern in self.instruction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0)
                
                memory = {
                    "type": MemoryType.INSTRUCTION.value,
                    "content": content,
                    "key": "instruction",
                    "value": match.group(1) if match.groups() else content,
                    "confidence": self._calculate_confidence(content, pattern),
                    "raw_text": text
                }
                memories.append(memory)
        
        return memories
    
    def _extract_entities(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract named entities (simplified - can be enhanced with NER)"""
        memories = []
        
        # Simple entity extraction - names, places, organizations
        # Look for capitalized sequences
        entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.finditer(entity_pattern, text)
        
        for match in matches:
            entity = match.group(1)
            # Filter out common words
            if entity.lower() not in ['i', 'my', 'the', 'a', 'an']:
                memory = {
                    "type": MemoryType.ENTITY.value,
                    "content": entity,
                    "key": "entity_name",
                    "value": entity,
                    "confidence": 0.7,
                    "raw_text": text
                }
                memories.append(memory)
        
        return memories
    
    def _extract_facts(self, text: str, turn_number: int) -> List[Dict[str, Any]]:
        """Extract factual statements"""
        memories = []
        
        # Look for "is", "are", "was", "were" patterns
        fact_patterns = [
            r"(.+)\s+(?:is|are|was|were)\s+(.+)",
            r"my\s+(.+)",
        ]
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0)
                
                # Avoid duplicating other memory types
                if len(content) > 10 and len(content.split()) > 2:
                    memory = {
                        "type": MemoryType.FACT.value,
                        "content": content,
                        "key": "fact",
                        "value": content,
                        "confidence": 0.6,
                        "raw_text": text
                    }
                    memories.append(memory)
        
        return memories
    
    def _parse_preference(self, text: str) -> tuple:
        """Parse preference into key-value pair"""
        # Try to extract structured preference
        patterns = [
            (r"language\s+is\s+(\w+)", ("language", 1)),
            (r"prefer[s]?\s+(.+)", ("preference", 1)),
            (r"favorite\s+(.+)", ("favorite", 1)),
            (r"call me\s+(.+)", ("name", 1)),
        ]
        
        for pattern, (key, group) in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return key, match.group(group)
        
        return "general", text
    
    def _extract_constraint_key(self, text: str) -> str:
        """Extract constraint type"""
        if re.search(r"time|am|pm|\d+:\d+", text, re.IGNORECASE):
            return "time_constraint"
        elif re.search(r"not available|busy", text, re.IGNORECASE):
            return "availability"
        else:
            return "general_constraint"
    
    def _calculate_confidence(self, content: str, pattern: str) -> float:
        """
        Calculate confidence score for extracted memory
        Higher confidence for more specific patterns
        """
        base_confidence = 0.8
        
        # Adjust based on content length and specificity
        if len(content) < 5:
            base_confidence -= 0.2
        
        # Boost confidence for specific patterns
        if re.search(r"language|prefer|favorite", content, re.IGNORECASE):
            base_confidence += 0.1
        
        return min(0.99, max(0.5, base_confidence))
    
    def filter_memories(
        self, 
        memories: List[Dict[str, Any]], 
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Filter memories by confidence threshold"""
        return [m for m in memories if m.get("confidence", 0) >= min_confidence]
    
    def deduplicate_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar memories"""
        seen = set()
        unique_memories = []
        
        for memory in memories:
            # Create a simple fingerprint
            fingerprint = f"{memory['type']}:{memory['key']}:{memory['value']}"
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_memories.append(memory)
        
        return unique_memories


# Example usage
if __name__ == "__main__":
    extractor = MemoryExtractor()
    
    # Test extraction
    test_message = "My preferred language is Kannada. Please call me after 11 AM."
    memories = extractor.extract_memories(
        user_message=test_message,
        assistant_response="I'll remember that!",
        turn_number=1,
        session_id="test_session"
    )
    
    print(f"Extracted {len(memories)} memories:")
    for memory in memories:
        print(json.dumps(memory, indent=2))