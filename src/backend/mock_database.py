"""
Mock database implementation for development and testing
when MongoDB is not available
"""

from argon2 import PasswordHasher
import copy


class MockCollection:
    """Mock MongoDB collection for testing"""
    
    def __init__(self, initial_data=None):
        self.data = {}
        if initial_data:
            for item in initial_data:
                self.data[item["_id"]] = copy.deepcopy(item)
    
    def find(self, query=None):
        """Find documents matching query"""
        if not query:
            return [{"_id": k, **v} for k, v in self.data.items()]
        
        results = []
        for doc_id, doc in self.data.items():
            if self._matches_query(doc, query):
                results.append({"_id": doc_id, **doc})
        return results
    
    def find_one(self, query):
        """Find one document matching query"""
        if isinstance(query, dict) and "_id" in query:
            doc_id = query["_id"]
            if doc_id in self.data:
                return {"_id": doc_id, **self.data[doc_id]}
            return None
        
        for doc_id, doc in self.data.items():
            if self._matches_query(doc, query):
                return {"_id": doc_id, **doc}
        return None
    
    def insert_one(self, document):
        """Insert a document"""
        doc_id = document["_id"]
        doc_copy = copy.deepcopy(document)
        del doc_copy["_id"]
        self.data[doc_id] = doc_copy
        return type('obj', (object,), {'inserted_id': doc_id})
    
    def update_one(self, query, update):
        """Update one document"""
        doc = self.find_one(query)
        if not doc:
            return type('obj', (object,), {'modified_count': 0})
        
        doc_id = doc["_id"]
        if "$push" in update:
            for field, value in update["$push"].items():
                if field not in self.data[doc_id]:
                    self.data[doc_id][field] = []
                self.data[doc_id][field].append(value)
        
        if "$pull" in update:
            for field, value in update["$pull"].items():
                if field in self.data[doc_id] and isinstance(self.data[doc_id][field], list):
                    if value in self.data[doc_id][field]:
                        self.data[doc_id][field].remove(value)
        
        return type('obj', (object,), {'modified_count': 1})
    
    def count_documents(self, query=None):
        """Count documents matching query"""
        return len(self.find(query or {}))
    
    def aggregate(self, pipeline):
        """Basic aggregation support"""
        # This is a simplified implementation for the specific use case
        results = []
        if len(pipeline) >= 2 and pipeline[0].get("$unwind") and pipeline[1].get("$group"):
            unwind_field = pipeline[0]["$unwind"].replace("$", "")
            
            # For schedule_details.days aggregation
            if unwind_field == "schedule_details.days":
                days = set()
                for doc in self.data.values():
                    if "schedule_details" in doc and "days" in doc["schedule_details"]:
                        for day in doc["schedule_details"]["days"]:
                            days.add(day)
                
                # Sort days in logical order
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                sorted_days = sorted(days, key=lambda x: day_order.index(x) if x in day_order else 999)
                
                for day in sorted_days:
                    results.append({"_id": day})
        
        return results
    
    def _matches_query(self, doc, query):
        """Check if document matches query"""
        for key, value in query.items():
            if "." in key:
                # Handle nested fields like "schedule_details.days"
                keys = key.split(".")
                current = doc
                for k in keys[:-1]:
                    if k not in current:
                        return False
                    current = current[k]
                
                final_key = keys[-1]
                if final_key not in current:
                    return False
                
                # Handle operators like $in
                if isinstance(value, dict):
                    if "$in" in value:
                        if not isinstance(current[final_key], list):
                            return False
                        return any(item in current[final_key] for item in value["$in"])
                    elif "$gte" in value:
                        return current[final_key] >= value["$gte"]
                    elif "$lte" in value:
                        return current[final_key] <= value["$lte"]
                else:
                    return current[final_key] == value
            else:
                if key not in doc:
                    return False
                if isinstance(value, dict):
                    # Handle operators
                    for op, op_value in value.items():
                        if op == "$gte":
                            if doc[key] < op_value:
                                return False
                        elif op == "$lte":
                            if doc[key] > op_value:
                                return False
                        elif op == "$in":
                            if doc[key] not in op_value:
                                return False
                else:
                    if doc[key] != value:
                        return False
        return True


# Mock database initialization
def init_mock_database():
    """Initialize mock database with sample data"""
    
    # Hash password function
    def hash_password(password):
        ph = PasswordHasher()
        return ph.hash(password)
    
    # Initial activities data
    initial_activities = [
        {
            "_id": "Chess Club",
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
            "schedule_details": {
                "days": ["Monday", "Friday"],
                "start_time": "15:15",
                "end_time": "16:45"
            },
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        {
            "_id": "Programming Class",
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
            "schedule_details": {
                "days": ["Tuesday", "Thursday"],
                "start_time": "07:00",
                "end_time": "08:00"
            },
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        {
            "_id": "Morning Fitness",
            "description": "Early morning physical training and exercises",
            "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
            "schedule_details": {
                "days": ["Monday", "Wednesday", "Friday"],
                "start_time": "06:30",
                "end_time": "07:45"
            },
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        {
            "_id": "Soccer Team",
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
            "schedule_details": {
                "days": ["Tuesday", "Thursday"],
                "start_time": "15:30",
                "end_time": "17:30"
            },
            "max_participants": 22,
            "participants": ["liam@mergington.edu", "noah@mergington.edu"]
        },
        {
            "_id": "Basketball Team",
            "description": "Practice and compete in basketball tournaments",
            "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
            "schedule_details": {
                "days": ["Wednesday", "Friday"],
                "start_time": "15:15",
                "end_time": "17:00"
            },
            "max_participants": 15,
            "participants": ["ava@mergington.edu", "mia@mergington.edu"]
        },
        {
            "_id": "Art Club",
            "description": "Explore various art techniques and create masterpieces",
            "schedule": "Thursdays, 3:15 PM - 5:00 PM",
            "schedule_details": {
                "days": ["Thursday"],
                "start_time": "15:15",
                "end_time": "17:00"
            },
            "max_participants": 15,
            "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
        },
        {
            "_id": "Drama Club",
            "description": "Act, direct, and produce plays and performances",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
            "schedule_details": {
                "days": ["Monday", "Wednesday"],
                "start_time": "15:30",
                "end_time": "17:30"
            },
            "max_participants": 20,
            "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
        },
        {
            "_id": "Math Club",
            "description": "Solve challenging problems and prepare for math competitions",
            "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
            "schedule_details": {
                "days": ["Tuesday"],
                "start_time": "07:15",
                "end_time": "08:00"
            },
            "max_participants": 10,
            "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
        },
        {
            "_id": "Debate Team",
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Fridays, 3:30 PM - 5:30 PM",
            "schedule_details": {
                "days": ["Friday"],
                "start_time": "15:30",
                "end_time": "17:30"
            },
            "max_participants": 12,
            "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
        },
        {
            "_id": "Weekend Robotics Workshop",
            "description": "Build and program robots in our state-of-the-art workshop",
            "schedule": "Saturdays, 10:00 AM - 2:00 PM",
            "schedule_details": {
                "days": ["Saturday"],
                "start_time": "10:00",
                "end_time": "14:00"
            },
            "max_participants": 15,
            "participants": ["ethan@mergington.edu", "oliver@mergington.edu"]
        },
        {
            "_id": "Science Olympiad",
            "description": "Weekend science competition preparation for regional and state events",
            "schedule": "Saturdays, 1:00 PM - 4:00 PM",
            "schedule_details": {
                "days": ["Saturday"],
                "start_time": "13:00",
                "end_time": "16:00"
            },
            "max_participants": 18,
            "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
        },
        {
            "_id": "Sunday Chess Tournament",
            "description": "Weekly tournament for serious chess players with rankings",
            "schedule": "Sundays, 2:00 PM - 5:00 PM",
            "schedule_details": {
                "days": ["Sunday"],
                "start_time": "14:00",
                "end_time": "17:00"
            },
            "max_participants": 16,
            "participants": ["william@mergington.edu", "jacob@mergington.edu"]
        },
        {
            "_id": "Manga Maniacs",
            "description": "Explore the fantastic stories of the most interesting characters from Japanese Manga (graphic novels)",
            "schedule": "Tuesdays, 7:00 PM - 8:00 PM",
            "schedule_details": {
                "days": ["Tuesday"],
                "start_time": "19:00",
                "end_time": "20:00"
            },
            "max_participants": 15,
            "participants": []
        }
    ]

    # Initial teachers data
    initial_teachers = [
        {
            "_id": "mrodriguez",
            "display_name": "Ms. Rodriguez",
            "password": hash_password("art123"),
            "role": "teacher"
        },
        {
            "_id": "mchen",
            "display_name": "Mr. Chen",
            "password": hash_password("chess456"),
            "role": "teacher"
        },
        {
            "_id": "principal",
            "display_name": "Principal Martinez",
            "password": hash_password("admin789"),
            "role": "admin"
        }
    ]

    # Create mock collections
    activities_collection = MockCollection(initial_activities)
    teachers_collection = MockCollection(initial_teachers)
    
    return activities_collection, teachers_collection