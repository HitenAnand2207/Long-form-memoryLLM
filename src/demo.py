"""
Interactive Demo for Long-Form Memory System
Demonstrates memory retention across 1,000+ turns
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from conversation_agent import ConversationAgent


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_turn(turn_num, user_msg, response_data):
    """Print formatted conversation turn"""
    print(f"\n{'─' * 70}")
    print(f"Turn {turn_num}")
    print(f"{'─' * 70}")
    print(f"👤 User: {user_msg}")
    print(f"🤖 Assistant: {response_data['assistant_response']}")
    
    if response_data.get('active_memories'):
        print(f"\n💭 Active Memories ({len(response_data['active_memories'])}):")
        for mem in response_data['active_memories']:
            print(f"   • {mem['content']} (turn {mem['origin_turn']}, relevance: {mem['relevance_score']:.2f})")
    
    if response_data.get('extracted_memories'):
        print(f"\n📝 New Memories ({len(response_data['extracted_memories'])}):")
        for mem in response_data['extracted_memories']:
            print(f"   • {mem['content']} [{mem['type']}] (confidence: {mem['confidence']:.2f})")
    
    print(f"\n⚡ Performance: {response_data['performance']['total_latency_ms']:.1f}ms")


def run_predefined_demo():
    """Run a predefined conversation demonstrating long-range memory"""
    print_header("PREDEFINED DEMO: Long-Range Memory Test")
    
    agent = ConversationAgent(verbose=False)
    session_id = f"demo_{int(time.time())}"
    
    # Conversation script with memory tests at different ranges
    conversation = [
        # Early turns - setting up memories
        ("My name is Priya and my preferred language is Kannada", 1),
        ("I work at TechCorp as a software engineer", 2),
        ("Please only call me after 11 AM on weekdays", 3),
        ("My favorite programming language is Python", 4),
        ("I have a meeting every Monday at 2 PM", 5),
        
        # Middle turns - casual conversation
        ("What's the weather like?", 50),
        ("Can you help me with a coding question?", 75),
        ("I need to schedule something", 100),
        
        # Test memory at turn 250
        ("Hello! What was my name again?", 250),
        
        # More conversation
        ("Tell me about cloud computing", 300),
        ("How do I optimize a database query?", 400),
        ("What are best practices for API design?", 500),
        
        # Test memory at turn 600
        ("What language do I prefer?", 600),
        
        # Continue
        ("Explain machine learning basics", 700),
        ("What's your opinion on microservices?", 800),
        ("How does blockchain work?", 900),
        
        # Critical test at turn 937 (from problem statement)
        ("Can you call me tomorrow?", 937),
        
        # Final test at turn 1000
        ("Remind me what job I have?", 1000),
    ]
    
    print(f"\nSession ID: {session_id}")
    print(f"Testing memory across {len(conversation)} turns (up to turn 1000)")
    
    for user_msg, turn_num in conversation:
        response = agent.process_turn(
            session_id=session_id,
            user_message=user_msg,
            turn_number=turn_num
        )
        
        # Print detailed output for memory test turns
        if turn_num in [1, 3, 250, 600, 937, 1000]:
            print_turn(turn_num, user_msg, response)
        else:
            # Brief output for other turns
            print(f"Turn {turn_num}: Processed in {response['performance']['total_latency_ms']:.1f}ms")
    
    # Print final summary
    print_header("SESSION SUMMARY")
    summary = agent.get_session_summary(session_id)
    
    print(f"\n📊 Statistics:")
    print(f"   Total Turns: {summary['total_turns']}")
    print(f"   Total Memories: {summary['memory_stats']['total_memories']}")
    print(f"   Average Confidence: {summary['memory_stats']['avg_confidence']:.2f}")
    print(f"   Memory Range: Turn {summary['memory_stats']['earliest_turn']} to {summary['memory_stats']['latest_turn']}")
    
    print(f"\n📈 Memory Types:")
    for mem_type, count in summary['retrieval_stats']['type_distribution'].items():
        print(f"   {mem_type.title()}: {count}")
    
    agent.close()


def run_interactive_demo():
    """Run interactive conversation mode"""
    print_header("INTERACTIVE MODE")
    
    agent = ConversationAgent(verbose=True)
    session_id = f"interactive_{int(time.time())}"
    
    print(f"\nSession ID: {session_id}")
    print("\nStart chatting! The system will remember important information.")
    print("Commands:")
    print("  'exit' or 'quit' - End session")
    print("  'stats' - Show memory statistics")
    print("  'memories' - List all memories")
    print("  'clear' - Clear all memories")
    
    turn_num = 0
    
    while True:
        try:
            user_input = input(f"\n[Turn {turn_num + 1}] You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'stats':
                summary = agent.get_session_summary(session_id)
                print(json.dumps(summary, indent=2))
                continue
            
            if user_input.lower() == 'memories':
                memories = agent.storage.get_session_memories(session_id)
                print(f"\n📚 All Memories ({len(memories)}):")
                for mem in memories:
                    print(f"   Turn {mem['source_turn']}: {mem['content']} [{mem['type']}]")
                continue
            
            if user_input.lower() == 'clear':
                agent.clear_session(session_id)
                turn_num = 0
                print("✓ Memories cleared")
                continue
            
            turn_num += 1
            
            response = agent.process_turn(
                session_id=session_id,
                user_message=user_input,
                turn_number=turn_num
            )
            
            print(f"\nAssistant: {response['assistant_response']}")
            
            if response.get('active_memories'):
                print(f"\n💭 Using {len(response['active_memories'])} memories from previous turns")
            
            if response.get('extracted_memories'):
                print(f"📝 Saved {len(response['extracted_memories'])} new memories")
        
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    agent.close()


def run_benchmark():
    """Run performance benchmark"""
    print_header("PERFORMANCE BENCHMARK")
    
    agent = ConversationAgent(verbose=False)
    session_id = f"benchmark_{int(time.time())}"
    
    print("\nTesting system performance across 1000 turns...")
    
    # Generate test messages
    test_messages = [
        "My name is Test User",
        "I prefer English",
        "Call me after 5 PM",
        "I work at Company XYZ",
        "My email is test@example.com"
    ]
    
    latencies = []
    memory_counts = []
    
    num_turns = 1000
    print_interval = 100
    
    start_time = time.time()
    
    for turn in range(1, num_turns + 1):
        # Cycle through test messages
        msg = test_messages[(turn - 1) % len(test_messages)] + f" (turn {turn})"
        
        response = agent.process_turn(
            session_id=session_id,
            user_message=msg,
            turn_number=turn
        )
        
        latencies.append(response['performance']['total_latency_ms'])
        memory_counts.append(len(response.get('active_memories', [])))
        
        if turn % print_interval == 0:
            avg_latency = sum(latencies[-print_interval:]) / print_interval
            print(f"Turn {turn}: Avg latency = {avg_latency:.1f}ms")
    
    total_time = time.time() - start_time
    
    # Results
    print_header("BENCHMARK RESULTS")
    
    print(f"\n⚡ Performance Metrics:")
    print(f"   Total Turns: {num_turns}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Avg Time per Turn: {(total_time / num_turns) * 1000:.1f}ms")
    print(f"   Min Latency: {min(latencies):.1f}ms")
    print(f"   Max Latency: {max(latencies):.1f}ms")
    print(f"   Avg Latency: {sum(latencies) / len(latencies):.1f}ms")
    
    summary = agent.get_session_summary(session_id)
    print(f"\n📊 Memory Statistics:")
    print(f"   Total Memories Stored: {summary['memory_stats']['total_memories']}")
    print(f"   Avg Memories Retrieved: {sum(memory_counts) / len(memory_counts):.1f}")
    
    agent.close()


def main():
    """Main entry point"""
    print_header("Long-Form Memory System Demo")
    
    print("\nChoose a demo mode:")
    print("  1. Predefined conversation (demonstrates long-range memory)")
    print("  2. Interactive mode (chat freely)")
    print("  3. Performance benchmark (1000 turns)")
    print("  0. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            run_predefined_demo()
        elif choice == '2':
            run_interactive_demo()
        elif choice == '3':
            run_benchmark()
        elif choice == '0':
            print("Goodbye!")
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    main()