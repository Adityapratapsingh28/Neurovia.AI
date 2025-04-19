import datetime
import uuid
from typing import Dict, List, Any, Optional

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
            "medications": self.medications,
            "chat_history": [msg.to_dict() for msg in self.chat_history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        user = cls(data["user_id"], data["name"], data["email"], data["dob"])
        user.health_data = data.get("health_data", {})
        user.appointments = data.get("appointments", [])
        user.medications = data.get("medications", [])
        user.chat_history = [ChatMessage.from_dict(msg) for msg in data.get("chat_history", [])]
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
        self.sender = sender
        self.message = message
        self.timestamp = timestamp
        
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        return cls(
            data["sender"],
            data["message"],
            datetime.datetime.fromisoformat(data["timestamp"])
        )