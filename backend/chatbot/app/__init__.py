from flask import Flask
from .models import User, Appointment, Medication, ChatMessage
from .store import DataStore
from .nlp import NLPEngine
from .dialog import DialogManager
from .security import SecurityManager

def create_app():
    app = Flask(__name__)
    
    # Initialize components
    data_store = DataStore()
    nlp_engine = NLPEngine(data_store)
    dialog_manager = DialogManager(data_store, nlp_engine)
    security_manager = SecurityManager()
    
    # Register routes
    from .main import init_routes
    init_routes(app, dialog_manager, security_manager)
    
    return app