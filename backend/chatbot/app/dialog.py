from typing import Optional
from .store import DataStore
from .nlp import NLPEngine
from .models import User, ChatMessage
import datetime
import uuid

class DialogManager:
    def __init__(self, data_store: DataStore, nlp_engine: NLPEngine):
        self.data_store = data_store
        self.nlp_engine = nlp_engine
        self.session_data = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        if user_id not in self.session_data:
            self.session_data[user_id] = {
                "context": {},
                "last_intent": None,
                "conversation_state": "greeting"
            }
        
        session = self.session_data[user_id]
        user = self.data_store.get_user(user_id)
        
        intent, confidence = self.nlp_engine.detect_intent(message)
        entities = self.nlp_engine.extract_entities(message, intent)
        
        session["last_intent"] = intent
        session["context"].update(entities)
        
        if intent == "greeting":
            if user:
                return f"Hello {user.name}! How can I help you with your healthcare needs today?"
            else:
                session["conversation_state"] = "onboarding_name"
                return "Welcome to Healthcare Assistant! I'd like to get to know you. What's your name?"
        
        elif intent == "emergency":
            return "⚠️ This sounds like a medical emergency. Please call emergency services (911) immediately or go to the nearest emergency room. ⚠️"
        
        elif intent == "appointment":
            if "date" in entities and "time" in entities:
                return f"I've noted your request for an appointment on {entities['date']} at {entities['time']}. Would you like me to schedule this for you?"
            else:
                return "I'd be happy to help you schedule an appointment. What day and time works best for you?"
        
        elif intent == "medication":
            if user and user.medications:
                meds = ", ".join([med["name"] for med in user.medications])
                return f"I see you're currently taking: {meds}. Would you like information about these medications or help setting up reminders?"
            else:
                return "I can help you manage your medications. Would you like to add a new medication or set up reminders?"
        
        elif intent == "symptom":
            if "symptoms" in entities and entities["symptoms"]:
                symptoms = ", ".join(entities["symptoms"])
                for condition, data in self.data_store.knowledge_base["common_conditions"].items():
                    matching_symptoms = set(entities["symptoms"]).intersection(set(data["symptoms"]))
                    if matching_symptoms and len(matching_symptoms) >= 2:
                        advice = data["self_care"]
                        return f"Based on your symptoms ({symptoms}), you may have a {condition}. {advice}\n\nWould you like to schedule an appointment with a doctor?"
                return f"I notice you mentioned these symptoms: {symptoms}. These symptoms could be related to several conditions. Would you like to schedule an appointment to discuss these with a healthcare provider?"
            else:
                return "I'm sorry to hear you're not feeling well. Can you tell me more about your symptoms?"
        
        elif intent == "health_data":
            return "I can help you track your health data. What type of data would you like to record or view (blood pressure, weight, glucose levels, etc.)?"
        
        if session["conversation_state"] == "onboarding_name" and intent != "greeting":
            session["context"]["name"] = message
            session["conversation_state"] = "onboarding_email"
            return f"Nice to meet you, {message}! What's your email address so I can create an account for you?"
        
        elif session["conversation_state"] == "onboarding_email":
            session["context"]["email"] = message
            session["conversation_state"] = "onboarding_dob"
            return "Thank you! For your health records, I need your date of birth (MM/DD/YYYY):"
        
        elif session["conversation_state"] == "onboarding_dob":
            session["context"]["dob"] = message
            session["conversation_state"] = "normal"
            new_user_id = str(uuid.uuid4())
            new_user = User(
                new_user_id, 
                session["context"]["name"],
                session["context"]["email"],
                session["context"]["dob"]
            )
            self.data_store.create_user(new_user)
            return f"Thank you! Your healthcare account has been created. How can I help you today?"
        
        return "I'm here to help with your healthcare needs. You can ask me about appointments, medications, symptoms, or health tracking."