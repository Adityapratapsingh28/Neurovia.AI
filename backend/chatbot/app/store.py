from typing import Dict, List, Optional
from .models import User

class DataStore:
    def __init__(self):
        self.users = {}
        self.knowledge_base = self._load_knowledge_base()
        self.intent_patterns = self._load_intent_patterns()
        
    def _load_knowledge_base(self) -> Dict:
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
        self.users[user.user_id] = user
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def update_user(self, user: User) -> None:
        self.users[user.user_id] = user