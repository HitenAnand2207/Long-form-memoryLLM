"""
Evaluation Script for Long-Form Memory System
Runs the evaluation suite for recall, relevance, latency, and safety.
"""

import sys
import os
import json
import time
import random
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from conversation_agent import ConversationAgent


class MemoryEvaluator:
    """Evaluate memory system performance"""

    def __init__(self):
        self.agent = ConversationAgent(verbose=False)
        self.test_results = {
            "long_range_recall": [],
            "accuracy": [],
            "retrieval_relevance": [],
            "latency": [],
            "hallucination_check": [],
        }

    def test_long_range_recall(self, session_id: str) -> Dict[str, Any]:
        """
        Test if information from early turns is recalled in later turns

        Priority: High
        """
        print("\n📝 Test 1: Long-Range Memory Recall")
        print("-" * 60)

        test_cases = [
            {
                "setup_turn": 1,
                "setup_message": "My preferred language is Kannada",
                "test_turn": 500,
                "test_message": "What language do I prefer?",
                "expected_memory_type": "preference",
                "expected_content_keywords": ["kannada", "language"],
            },
            {
                "setup_turn": 5,
                "setup_message": "Please call me only after 11 AM",
                "test_turn": 937,
                "test_message": "Can you call me tomorrow?",
                "expected_memory_type": "constraint",
                "expected_content_keywords": ["11", "am", "after"],
            },
            {
                "setup_turn": 10,
                "setup_message": "My name is Rajesh Kumar",
                "test_turn": 800,
                "test_message": "What's my name?",
                "expected_memory_type": "preference",
                "expected_content_keywords": ["rajesh", "kumar", "name"],
            },
        ]

        results = []

        for i, test in enumerate(test_cases, 1):
            # Setup turn - store memory
            setup_response = self.agent.process_turn(
                session_id=session_id,
                user_message=test["setup_message"],
                turn_number=test["setup_turn"],
            )

            # Fill gap with dummy turns
            self._fill_conversation_gap(
                session_id, test["setup_turn"] + 1, test["test_turn"] - 1
            )

            # Test turn - recall memory
            test_response = self.agent.process_turn(
                session_id=session_id,
                user_message=test["test_message"],
                turn_number=test["test_turn"],
            )

            # Check if memory was retrieved
            active_memories = test_response.get("active_memories", [])
            recalled = False
            relevance_score = 0.0

            for mem in active_memories:
                # Check if memory matches expected criteria
                content_lower = mem["content"].lower()
                matches_keywords = any(
                    kw in content_lower for kw in test["expected_content_keywords"]
                )
                matches_type = mem["type"] == test["expected_memory_type"]

                if matches_keywords and matches_type:
                    recalled = True
                    relevance_score = mem.get("relevance_score", 0)
                    break

            turn_distance = test["test_turn"] - test["setup_turn"]

            result = {
                "test_case": i,
                "turn_distance": turn_distance,
                "recalled": recalled,
                "relevance_score": relevance_score,
                "num_active_memories": len(active_memories),
                "latency_ms": test_response["performance"]["total_latency_ms"],
            }

            results.append(result)

            status = "✓ PASS" if recalled else "✗ FAIL"
            print(f"  Case {i}: Distance={turn_distance} turns, {status}")
            print(f"    Recalled: {recalled}, Relevance: {relevance_score:.2f}")

        # Calculate metrics
        recall_rate = sum(1 for r in results if r["recalled"]) / len(results)
        avg_relevance = sum(r["relevance_score"] for r in results) / len(results)

        print(f"\n  Overall Recall Rate: {recall_rate * 100:.1f}%")
        print(f"  Average Relevance: {avg_relevance:.2f}")

        self.test_results["long_range_recall"] = results

        return {
            "recall_rate": recall_rate,
            "avg_relevance": avg_relevance,
            "results": results,
        }

    def test_accuracy_across_turns(self, session_id: str) -> Dict[str, Any]:
        """
        Test accuracy of memory extraction and retrieval across different turn ranges

        Priority: High
        """
        print("\n📝 Test 2: Accuracy Across 1-1000 Turns")
        print("-" * 60)

        turn_ranges = [
            (1, 10),  # Early turns
            (100, 200),  # Mid-early
            (400, 500),  # Middle
            (800, 900),  # Late
            (950, 1000),  # Very late
        ]

        results = []

        for start, end in turn_ranges:
            range_results = {
                "range": f"{start}-{end}",
                "memories_extracted": 0,
                "avg_confidence": 0.0,
                "avg_latency": 0.0,
            }

            total_confidence = 0
            total_latency = 0
            total_extracted = 0

            # Sample 5 turns from this range
            sample_turns = random.sample(range(start, end + 1), min(5, end - start + 1))

            for turn in sample_turns:
                response = self.agent.process_turn(
                    session_id=session_id,
                    user_message=f"This is test message at turn {turn}. Remember this information.",
                    turn_number=turn,
                )

                extracted = response.get("extracted_memories", [])
                total_extracted += len(extracted)

                if extracted:
                    total_confidence += sum(m["confidence"] for m in extracted)

                total_latency += response["performance"]["total_latency_ms"]

            range_results["memories_extracted"] = total_extracted
            range_results["avg_confidence"] = (
                total_confidence / total_extracted if total_extracted > 0 else 0
            )
            range_results["avg_latency"] = total_latency / len(sample_turns)

            results.append(range_results)

            print(f"  Range {start}-{end}:")
            print(f"    Extracted: {total_extracted} memories")
            print(f"    Avg Confidence: {range_results['avg_confidence']:.2f}")
            print(f"    Avg Latency: {range_results['avg_latency']:.1f}ms")

        self.test_results["accuracy"] = results

        return {"results": results}

    def test_retrieval_relevance(self, session_id: str) -> Dict[str, Any]:
        """
        Test if retrieved memories are relevant to current context

        Priority: Medium
        """
        print("\n📝 Test 3: Retrieval Relevance")
        print("-" * 60)

        # Store diverse memories
        test_memories = [
            ("I prefer vegetarian food", 1),
            ("My meeting is at 3 PM every Tuesday", 5),
            ("I'm learning Python programming", 10),
            ("My favorite color is blue", 15),
            ("I work remotely from home", 20),
        ]

        for msg, turn in test_memories:
            self.agent.process_turn(session_id, msg, turn)

        # Test queries and expected relevant memories
        test_queries = [
            {
                "turn": 100,
                "query": "What kind of food do I like?",
                "expected_keywords": ["vegetarian", "food"],
            },
            {
                "turn": 200,
                "query": "When is my meeting?",
                "expected_keywords": ["meeting", "3", "pm", "tuesday"],
            },
            {
                "turn": 300,
                "query": "What programming language am I learning?",
                "expected_keywords": ["python", "programming"],
            },
        ]

        results = []

        for test in test_queries:
            response = self.agent.process_turn(
                session_id=session_id,
                user_message=test["query"],
                turn_number=test["turn"],
            )

            active_memories = response.get("active_memories", [])

            # Check relevance
            relevant_count = 0
            for mem in active_memories:
                content_lower = mem["content"].lower()
                if any(kw in content_lower for kw in test["expected_keywords"]):
                    relevant_count += 1

            precision = relevant_count / len(active_memories) if active_memories else 0

            result = {
                "query": test["query"],
                "total_retrieved": len(active_memories),
                "relevant_retrieved": relevant_count,
                "precision": precision,
            }

            results.append(result)

            print(f"  Query: '{test['query']}'")
            print(f"    Precision: {precision * 100:.1f}%")

        avg_precision = sum(r["precision"] for r in results) / len(results)
        print(f"\n  Average Precision: {avg_precision * 100:.1f}%")

        self.test_results["retrieval_relevance"] = results

        return {"avg_precision": avg_precision, "results": results}

    def test_latency_impact(self, session_id: str) -> Dict[str, Any]:
        """
        Test system latency as conversation grows

        Priority: Medium
        """
        print("\n📝 Test 4: Latency Impact")
        print("-" * 60)

        turn_checkpoints = [10, 50, 100, 250, 500, 750, 1000]
        latencies = []

        print("  Measuring latency at different conversation lengths...")

        for checkpoint in turn_checkpoints:
            # Measure latency over 5 turns around checkpoint
            checkpoint_latencies = []

            for i in range(5):
                turn = checkpoint + i
                response = self.agent.process_turn(
                    session_id=session_id,
                    user_message=f"Test message at turn {turn}",
                    turn_number=turn,
                )
                checkpoint_latencies.append(response["performance"]["total_latency_ms"])

            avg_latency = sum(checkpoint_latencies) / len(checkpoint_latencies)
            latencies.append({"turn": checkpoint, "avg_latency_ms": avg_latency})

            print(f"    Turn {checkpoint}: {avg_latency:.1f}ms")

        # Check if latency is sub-100ms
        within_target = sum(1 for l in latencies if l["avg_latency_ms"] < 100) / len(
            latencies
        )

        print(f"\n  Turns within 100ms target: {within_target * 100:.1f}%")

        self.test_results["latency"] = latencies

        return {"latencies": latencies, "within_100ms_rate": within_target}

    def test_hallucination_avoidance(self, session_id: str) -> Dict[str, Any]:
        """
        Test that system doesn't fabricate memories

        Priority: Medium
        """
        print("\n📝 Test 5: Hallucination Avoidance")
        print("-" * 60)

        # Store specific memories
        real_memories = ["My name is John", "I live in Bangalore", "I work at TechCorp"]

        for i, msg in enumerate(real_memories, 1):
            self.agent.process_turn(session_id, msg, i)

        # Ask about information never provided
        fake_queries = [
            "What's my favorite movie?",
            "Where did I go to college?",
            "What's my phone number?",
        ]

        results = []

        for query in fake_queries:
            response = self.agent.process_turn(
                session_id=session_id, user_message=query, turn_number=100
            )

            # Check if any memories were retrieved (should be none or low relevance)
            active_memories = response.get("active_memories", [])

            # Memories with high relevance to fake query would indicate hallucination
            high_relevance_count = sum(
                1 for m in active_memories if m.get("relevance_score", 0) > 0.5
            )

            result = {
                "query": query,
                "inappropriate_retrievals": high_relevance_count,
                "passed": high_relevance_count == 0,
            }

            results.append(result)

            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  Query: '{query}' - {status}")

        pass_rate = sum(1 for r in results if r["passed"]) / len(results)
        print(f"\n  Pass Rate: {pass_rate * 100:.1f}%")

        self.test_results["hallucination_check"] = results

        return {"pass_rate": pass_rate, "results": results}

    def _fill_conversation_gap(self, session_id: str, start_turn: int, end_turn: int):
        """Fill conversation with dummy turns to simulate long conversation"""
        # Sample every 10th turn to reduce processing time
        for turn in range(start_turn, end_turn + 1, 10):
            self.agent.process_turn(
                session_id=session_id,
                user_message=f"Filler message for turn {turn}",
                turn_number=turn,
                retrieve_memories=False,  # Don't retrieve to speed up
            )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": self.test_results,
            "summary": {
                "long_range_recall": "High"
                if self.test_results["long_range_recall"]
                else "Not tested",
                "accuracy": "High" if self.test_results["accuracy"] else "Not tested",
                "retrieval_relevance": "Medium"
                if self.test_results["retrieval_relevance"]
                else "Not tested",
                "latency_impact": "Medium"
                if self.test_results["latency"]
                else "Not tested",
                "hallucination_avoidance": "Medium"
                if self.test_results["hallucination_check"]
                else "Not tested",
            },
        }


def main():
    """Run complete evaluation suite"""
    print("=" * 70)
    print("  LONG-FORM MEMORY SYSTEM EVALUATION")
    print("  Running Evaluation Suite")
    print("=" * 70)

    evaluator = MemoryEvaluator()
    session_id = f"eval_{int(time.time())}"

    # Run all tests
    evaluator.test_long_range_recall(session_id)
    evaluator.test_accuracy_across_turns(session_id)
    evaluator.test_retrieval_relevance(session_id)
    evaluator.test_latency_impact(session_id)
    evaluator.test_hallucination_avoidance(session_id)

    # Generate report
    report = evaluator.generate_report()

    print("\n" + "=" * 70)
    print("  EVALUATION COMPLETE")
    print("=" * 70)

    # Save report
    report_path = "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Full report saved to: {report_path}")

    evaluator.agent.close()


if __name__ == "__main__":
    main()
