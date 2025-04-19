from flask import Flask, request, jsonify
from app.dialog import DialogManager  # Changed from .dialog to app.dialog
from app.security import SecurityManager  # Changed from .security to app.security
from app.models import ChatMessage  # Changed from .models to app.models
import datetime

def init_routes(app: Flask, dialog_manager: DialogManager, security_manager: SecurityManager):
    active_sessions = {}

    @app.route('/api/message', methods=['POST'])
    def process_message():
        data = request.get_json()
        session_token = request.headers.get('X-Session-Token')
        message = data.get('message', '')

        if not session_token or session_token not in active_sessions:
            temp_user_id = f"temp_{security_manager.generate_session_token()}"
            response = dialog_manager.process_message(temp_user_id, message)
            user = dialog_manager.data_store.get_user(temp_user_id)
            if user:
                user.chat_history.append(ChatMessage("user", message, datetime.datetime.now()))
                user.chat_history.append(ChatMessage("bot", response, datetime.datetime.now()))
                dialog_manager.data_store.update_user(user)
        else:
            user_id = active_sessions[session_token]
            response = dialog_manager.process_message(user_id, message)
            user = dialog_manager.data_store.get_user(user_id)
            if user:
                user.chat_history.append(ChatMessage("user", message, datetime.datetime.now()))
                user.chat_history.append(ChatMessage("bot", response, datetime.datetime.now()))
                dialog_manager.data_store.update_user(user)

        return jsonify({'response': response})

    @app.route('/api/authenticate', methods=['POST'])
    def authenticate():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        session_token = security_manager.generate_session_token()
        active_sessions[session_token] = f"user_{email}"
        return jsonify({'session_token': session_token})

if __name__ == '__main__':
    from app import create_app  # Changed from . to app
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)