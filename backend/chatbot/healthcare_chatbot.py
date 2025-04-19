import re
import json
import datetime
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple

# ======== Data Models ========

class User:
    def __init__(self, user_id: str, name: str, email: str, dob: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.dob = dob
        self.health_data = {}
        self.appointments = []
        self.medications = []
        self.chat_history = []
        
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "dob": self.dob,
            "health_data": self.health_data,
            "appointments": self.appointments,
            "medications": self.medications
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        user = cls(data["user_id"], data["name"], data["email"], data["dob"])
        user.health_data = data.get("health_data", {})
        user.appointments = data.get("appointments", [])
        user.medications = data.get("medications", [])
        return user


class Appointment:
    def __init__(self, doctor: str, date_time: datetime.datetime, reason: str):
        self.appointment_id = str(uuid.uuid4())
        self.doctor = doctor
        self.date_time = date_time
        self.reason = reason
        self.status = "scheduled"
        
    def to_dict(self) -> Dict:
        return {
            "appointment_id": self.appointment_id,
            "doctor": self.doctor,
            "date_time": self.date_time.isoformat(),
            "reason": self.reason,
            "status": self.status
        }


class Medication:
    def __init__(self, name: str, dosage: str, frequency: str, start_date: datetime.date):
        self.medication_id = str(uuid.uuid4())
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.start_date = start_date
        self.end_date = None
        
    def to_dict(self) -> Dict:
        return {
            "medication_id": self.medication_id,
            "name": self.name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None
        }


class ChatMessage:
    def __init__(self, sender: str, message: str, timestamp: datetime.datetime):
        self.message_id = str(uuid.uuid4())
        self.sender = sender  # "user" or "bot"
        self.message = message
        self.timestamp = timestamp
        
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


# ======== Storage Layer ========

class DataStore:
    """Simple in-memory data store for demo purposes. In production, use a secure database."""
    
    def __init__(self):
        self.users = {}
        self.knowledge_base = self._load_knowledge_base()
        self.intent_patterns = self._load_intent_patterns()
        
    def _load_knowledge_base(self) -> Dict:
        # In production, load from database or API
        return {
            "common_conditions": {
                "cold": {
                    "symptoms": ["runny nose", "sore throat", "cough", "congestion"],
                    "self_care": "Rest, drink fluids, and take over-the-counter cold medications as needed. Contact a doctor if symptoms persist beyond 10 days."
                },
                "flu": {
                    "symptoms": ["fever", "body aches", "fatigue", "cough"],
                    "self_care": "Rest, stay hydrated, and take fever reducers. Contact a doctor if you have difficulty breathing or symptoms are severe."
                }
            },
            "emergency_conditions": ["chest pain", "difficulty breathing", "severe bleeding", "sudden severe headache"]
        }
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        return {
            "greeting": [
                r"(?i)hello|hi|hey|greetings",
                r"(?i)good (morning|afternoon|evening)"
            ],
            "appointment": [
                r"(?i)schedule|book|make|set up.*appointment",
                r"(?i)see a doctor|visit|consultation"
            ],
            "medication": [
                r"(?i)medication|medicine|prescription|refill",
                r"(?i)remind.*take (my )?medication"
            ],
            "symptom": [
                r"(?i)I (have|am experiencing|feel|suffering from)",
                r"(?i)symptom|pain|discomfort|fever|cough|headache"
            ],
            "health_data": [
                r"(?i)track|record|log|monitor|update.*(blood pressure|weight|glucose|exercise)",
                r"(?i)my health (data|information|stats|numbers)"
            ]
        }
    
    def create_user(self, user: User) -> None:
        """Create a new user in the data store"""
        self.users[user.user_id] = user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return self.users.get(user_id)
    
    def update_user(self, user: User) -> None:
        """Update an existing user"""
        self.users[user.user_id] = user


# ======== Natural Language Processing ========

class NLPEngine:
    def __init__(self, data_store: DataStore):
        self.data_store = data_store
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """Detect the user's intent from their message"""
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, patterns in self.data_store.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message)
                if matches:
                    # Simple scoring based on number of matches
                    score = len(matches) / len(message.split())
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        # Emergency detection takes priority
        for emergency_term in self.data_store.knowledge_base["emergency_conditions"]:
            if emergency_term in message.lower():
                return "emergency", 1.0
                
        return best_intent, best_score
    
    def extract_entities(self, message: str, intent: str) -> Dict:
        """Extract relevant entities based on intent"""
        entities = {}
        
        if intent == "appointment":
            # Simple date/time extraction (not comprehensive)
            date_matches = re.findall(r'(?i)(?:on|for) (january|february|march|april|may|june|july|august|september|october|november|december) (\d{1,2})(?:st|nd|rd|th)?', message)
            if date_matches:
                entities["date"] = f"{date_matches[0][0]} {date_matches[0][1]}"
            
            time_matches = re.findall(r'(?i)(?:at) (\d{1,2})(?::(\d{2}))? ?(am|pm)', message)
            if time_matches:
                hour = int(time_matches[0][0])
                minute = time_matches[0][1] or "00"
                ampm = time_matches[0][2].lower()
                entities["time"] = f"{hour}:{minute} {ampm}"
            
            doctor_matches = re.findall(r'(?i)(?:with) (?:dr\.?) ([a-z]+)', message)
            if doctor_matches:
                entities["doctor"] = doctor_matches[0]
        
        elif intent == "symptom":
            for condition in self.data_store.knowledge_base["common_conditions"]:
                condition_data = self.data_store.knowledge_base["common_conditions"][condition]
                for symptom in condition_data["symptoms"]:
                    if symptom in message.lower():
                        if "symptoms" not in entities:
                            entities["symptoms"] = []
                        entities["symptoms"].append(symptom)
        
        return entities


# ======== Dialog Management ========

class DialogManager:
    def __init__(self, data_store: DataStore, nlp_engine: NLPEngine):
        self.data_store = data_store
        self.nlp_engine = nlp_engine
        self.session_data = {}  # Stores context for active conversations
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process an incoming message and generate a response"""
        # Get or create session data
        if user_id not in self.session_data:
            self.session_data[user_id] = {
                "context": {},
                "last_intent": None,
                "conversation_state": "greeting"
            }
        
        session = self.session_data[user_id]
        user = self.data_store.get_user(user_id)
        
        # Detect intent
        intent, confidence = self.nlp_engine.detect_intent(message)
        entities = self.nlp_engine.extract_entities(message, intent)
        
        # Update session context
        session["last_intent"] = intent
        session["context"].update(entities)
        
        # Handle different intents
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
        
        # Handle multi-turn conversation states
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
            # Create new user
            new_user_id = str(uuid.uuid4())
            new_user = User(
                new_user_id, 
                session["context"]["name"],
                session["context"]["email"],
                session["context"]["dob"]
            )
            self.data_store.create_user(new_user)
            return f"Thank you! Your healthcare account has been created. How can I help you today?"
        
        # Fallback response
        return "I'm here to help with your healthcare needs. You can ask me about appointments, medications, symptoms, or health tracking."


# ======== Security Layer ========

class SecurityManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return str(uuid.uuid4())
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """Encrypt sensitive data (simplified for demo)"""
        # In production, use proper encryption
        return f"ENCRYPTED_{data}"
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        """Decrypt sensitive data (simplified for demo)"""
        # In production, use proper decryption
        if encrypted_data.startswith("ENCRYPTED_"):
            return encrypted_data[10:]
        return encrypted_data


# ======== Chatbot Application ========

class HealthcareChatbot:
    def __init__(self):
        self.data_store = DataStore()
        self.nlp_engine = NLPEngine(self.data_store)
        self.dialog_manager = DialogManager(self.data_store, self.nlp_engine)
        self.security_manager = SecurityManager()
        self.active_sessions = {}  # Maps session tokens to user IDs
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate a user and return a session token"""
        # In a real system, look up user by email and verify password
        for user_id, user in self.data_store.users.items():
            if user.email == email:
                # Normally verify hashed password here
                session_token = self.security_manager.generate_session_token()
                self.active_sessions[session_token] = user_id
                return session_token
        return None
    
    def process_message(self, session_token: str, message: str) -> str:
        """Process a message from an authenticated session"""
        if session_token in self.active_sessions:
            user_id = self.active_sessions[session_token]
            response = self.dialog_manager.process_message(user_id, message)
            
            # Log the interaction
            user = self.data_store.get_user(user_id)
            if user:
                user.chat_history.append(
                    ChatMessage("user", message, datetime.datetime.now()).to_dict()
                )
                user.chat_history.append(
                    ChatMessage("bot", response, datetime.datetime.now()).to_dict()
                )
                self.data_store.update_user(user)
            
            return response
        else:
            # For demo purposes, handle unauthenticated users by creating a temporary ID
            temp_user_id = f"temp_{str(uuid.uuid4())}"
            response = self.dialog_manager.process_message(temp_user_id, message)
            return response


# ======== Example Usage ========

def demo():
    chatbot = HealthcareChatbot()
    print("Healthcare Chatbot Demo")
    print("Type 'exit' to quit")
    print("-" * 50)
    
    session_token = None  # Unauthenticated initially
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        
        response = chatbot.process_message(session_token, user_input)
        print(f"\nBot: {response}")


if __name__ == "__main__":
    demo()