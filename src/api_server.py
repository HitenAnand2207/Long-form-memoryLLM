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
agent = ConversationAgent(verbose=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "memory_enabled": agent.enable_memory
    })

@app.route('/conversation', methods=['POST'])
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
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'user_message' not in data:
            return jsonify({
                "error": "Missing required fields: session_id, user_message"
            }), 400
        
        session_id = data['session_id']
        user_message = data['user_message']
        turn_number = data.get('turn_number')
        retrieve_memories = data.get('retrieve_memories', True)
        
        # Process turn
        response = agent.process_turn(
            session_id=session_id,
            user_message=user_message,
            turn_number=turn_number,
            retrieve_memories=retrieve_memories
        )
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/memories/<session_id>', methods=['GET'])
def get_memories(session_id):
    """
    Get all memories for a session
    
    Query parameters:
    - type: Filter by memory type (optional)
    - min_confidence: Minimum confidence threshold (optional)
    """
    try:
        memory_type = request.args.get('type')
        min_confidence = float(request.args.get('min_confidence', 0.0))
        
        memories = agent.storage.get_session_memories(
            session_id=session_id,
            memory_type=memory_type,
            min_confidence=min_confidence
        )
        
        return jsonify({
            "session_id": session_id,
            "total_memories": len(memories),
            "memories": memories
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/session/<session_id>', methods=['GET'])
def get_session_summary(session_id):
    """Get session summary and statistics"""
    try:
        summary = agent.get_session_summary(session_id)
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/session/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear session and all its memories"""
    try:
        agent.clear_session(session_id)
        return jsonify({
            "message": f"Session {session_id} cleared successfully"
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/search', methods=['POST'])
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
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query"
            }), 400
        
        query = data['query']
        session_id = data.get('session_id')
        top_k = data.get('top_k', 5)
        
        results = agent.storage.search_memories_by_content(
            query=query,
            session_id=session_id,
            top_k=top_k
        )
        
        return jsonify({
            "query": query,
            "total_results": len(results),
            "results": results
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_global_stats():
    """Get global memory statistics"""
    try:
        stats = agent.storage.get_memory_stats()
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
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
    
    app.run(host='0.0.0.0', port=5000, debug=True)