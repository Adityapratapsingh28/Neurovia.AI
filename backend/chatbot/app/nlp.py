import re
from typing import Dict, Tuple
from .store import DataStore

class NLPEngine:
    def __init__(self, data_store: DataStore):
        self.data_store = data_store
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, patterns in self.data_store.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message)
                if matches:
                    score = len(matches) / len(message.split())
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        for emergency_term in self.data_store.knowledge_base["emergency_conditions"]:
            if emergency_term in message.lower():
                return "emergency", 1.0
                
        return best_intent, best_score
    
    def extract_entities(self, message: str, intent: str) -> Dict:
        entities = {}
        
        if intent == "appointment":
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