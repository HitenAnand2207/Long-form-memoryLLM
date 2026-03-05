"""
API Server for Long-Form Memory System
Provides REST endpoints for conversation processing
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from conversation_agent import ConversationAgent

app = Flask(__name__)
CORS(app)

# Initialize agent
agent = ConversationAgent(
    verbose=os.getenv("MEMORY_AGENT_VERBOSE", "false").lower() == "true"
)


def _json_error(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


def _require_memory_enabled():
    if not agent.enable_memory:
        return _json_error("Memory system is disabled", 503)
    return None


def _parse_positive_int(value, field_name: str, default: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")
    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return parsed


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "memory_enabled": agent.enable_memory})


@app.route("/conversation", methods=["POST"])
def process_conversation():
    """
    Process a conversation turn

    Request body:
    {
        "session_id": "string",
        "user_message": "string",
        "turn_number": int (optional),
        "retrieve_memories": bool (optional, default: true)
    }
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return _json_error("Request body must be valid JSON object")
        if "session_id" not in data or "user_message" not in data:
            return _json_error("Missing required fields: session_id, user_message")

        session_id = data["session_id"]
        user_message = data["user_message"]

        if not isinstance(session_id, str) or not session_id.strip():
            return _json_error("session_id must be a non-empty string")
        if not isinstance(user_message, str) or not user_message.strip():
            return _json_error("user_message must be a non-empty string")

        turn_number = data.get("turn_number")
        retrieve_memories = data.get("retrieve_memories", True)

        if turn_number is not None:
            try:
                turn_number = int(turn_number)
            except (TypeError, ValueError):
                return _json_error("turn_number must be an integer")
            if turn_number <= 0:
                return _json_error("turn_number must be > 0")

        if not isinstance(retrieve_memories, bool):
            return _json_error("retrieve_memories must be a boolean")

        # Process turn
        response = agent.process_turn(
            session_id=session_id,
            user_message=user_message,
            turn_number=turn_number,
            retrieve_memories=retrieve_memories,
        )

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/memories/<session_id>", methods=["GET"])
def get_memories(session_id):
    """
    Get all memories for a session

    Query parameters:
    - type: Filter by memory type (optional)
    - min_confidence: Minimum confidence threshold (optional)
    """
    try:
        memory_guard = _require_memory_enabled()
        if memory_guard:
            return memory_guard

        if not isinstance(session_id, str) or not session_id.strip():
            return _json_error("session_id must be a non-empty string")

        memory_type = request.args.get("type")
        try:
            min_confidence = float(request.args.get("min_confidence", 0.0))
        except ValueError:
            return _json_error("min_confidence must be a number between 0.0 and 1.0")
        if not 0.0 <= min_confidence <= 1.0:
            return _json_error("min_confidence must be between 0.0 and 1.0")

        memories = agent.storage.get_session_memories(
            session_id=session_id,
            memory_type=memory_type,
            min_confidence=min_confidence,
        )

        return jsonify(
            {
                "session_id": session_id,
                "total_memories": len(memories),
                "memories": memories,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/session/<session_id>", methods=["GET"])
def get_session_summary(session_id):
    """Get session summary and statistics"""
    try:
        summary = agent.get_session_summary(session_id)
        return jsonify(summary)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/session/<session_id>", methods=["DELETE"])
def clear_session(session_id):
    """Clear session and all its memories"""
    try:
        memory_guard = _require_memory_enabled()
        if memory_guard:
            return memory_guard

        agent.clear_session(session_id)
        return jsonify({"message": f"Session {session_id} cleared successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search_memories():
    """
    Search memories by content

    Request body:
    {
        "query": "string",
        "session_id": "string" (optional),
        "top_k": int (optional, default: 5)
    }
    """
    try:
        memory_guard = _require_memory_enabled()
        if memory_guard:
            return memory_guard

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return _json_error("Request body must be valid JSON object")
        if "query" not in data:
            return _json_error("Missing required field: query")

        query = data["query"]
        if not isinstance(query, str) or not query.strip():
            return _json_error("query must be a non-empty string")

        session_id = data.get("session_id")
        if session_id is not None and (
            not isinstance(session_id, str) or not session_id.strip()
        ):
            return _json_error("session_id must be a non-empty string when provided")

        try:
            top_k = _parse_positive_int(data.get("top_k"), "top_k", default=5)
        except ValueError as exc:
            return _json_error(str(exc))

        results = agent.storage.search_memories_by_content(
            query=query, session_id=session_id, top_k=top_k
        )

        return jsonify(
            {"query": query, "total_results": len(results), "results": results}
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def get_global_stats():
    """Get global memory statistics"""
    try:
        memory_guard = _require_memory_enabled()
        if memory_guard:
            return memory_guard

        stats = agent.storage.get_memory_stats()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("Long-Form Memory API Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET  /health                    - Health check")
    print("  POST /conversation              - Process conversation turn")
    print("  GET  /memories/<session_id>     - Get session memories")
    print("  GET  /session/<session_id>      - Get session summary")
    print("  DELETE /session/<session_id>    - Clear session")
    print("  POST /search                    - Search memories")
    print("  GET  /stats                     - Global statistics")
    print("\n" + "=" * 60)

    host = os.getenv("MEMORY_API_HOST", "0.0.0.0")
    port = int(os.getenv("MEMORY_API_PORT", "5000"))
    debug = os.getenv("MEMORY_API_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
