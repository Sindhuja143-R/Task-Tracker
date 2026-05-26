"""
Data Models and Storage Layer for Task Tracker
Handles task structure, validation, and persistence
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import json
import os


class Task:
    """Represents a single task with metadata"""
    
    def __init__(
        self,
        name: str,
        category: str = "Personal",
        priority: str = "Medium",
        done: bool = False,
        created_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        postponed_count: int = 0
    ):
        self.name = name
        self.category = category
        self.priority = priority
        self.done = done
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.postponed_count = postponed_count
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary for JSON storage"""
        return {
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "done": self.done,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "postponed_count": self.postponed_count
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Task':
        """Create task from dictionary, handling backward compatibility"""
        # Handle old format (just name and done)
        if "category" not in data:
            data["category"] = "Personal"
        if "priority" not in data:
            data["priority"] = "Medium"
        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()
        if "postponed_count" not in data:
            data["postponed_count"] = 0
        
        return Task(**data)


class DailyTaskData:
    """Represents all tasks for a single day"""
    
    def __init__(self, date_str: str, tasks: List[Task] = None):
        self.date_str = date_str
        self.tasks = tasks or []
    
    def add_task(self, task: Task):
        """Add a task to the day"""
        self.tasks.append(task)
    
    def get_completion_stats(self) -> Tuple[int, int]:
        """Return (completed_count, total_count)"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.done)
        return completed, total
    
    def get_completion_rate(self) -> float:
        """Return completion rate as percentage (0-100)"""
        completed, total = self.get_completion_stats()
        if total == 0:
            return 0.0
        return (completed / total) * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            "date": self.date_str,
            "tasks": [t.to_dict() for t in self.tasks],
            "completed": self.get_completion_stats()[0],
            "total": self.get_completion_stats()[1]
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'DailyTaskData':
        """Create from dictionary, handling backward compatibility"""
        date_str = data.get("date") or list(data.keys())[0] if isinstance(data, dict) else ""
        
        # Handle old format where date is key and value is list of task dicts
        if isinstance(data, list):
            tasks = [Task.from_dict(t) for t in data]
            return DailyTaskData(date_str, tasks)
        
        # Handle new format
        tasks_data = data.get("tasks", data) if isinstance(data.get("tasks"), list) else data
        if isinstance(tasks_data, list):
            tasks = [Task.from_dict(t) for t in tasks_data]
        else:
            tasks = []
        
        return DailyTaskData(date_str, tasks)


class DataStore:
    """Handles all data persistence and retrieval"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self._ensure_file_exists()
        self.data = self._load_data()
    
    def _ensure_file_exists(self):
        """Ensure the data file and directory exist"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _load_data(self) -> Dict:
        """Load data from JSON file with error handling"""
        if not os.path.exists(self.data_file):
            return {"tasks_data": {}, "metadata": {}}
        
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                # Ensure backward compatibility
                if "metadata" not in data:
                    data["metadata"] = {}
                return data
        except json.JSONDecodeError:
            return {"tasks_data": {}, "metadata": {}}
    
    def save(self):
        """Save data to JSON file"""
        self._ensure_file_exists()
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def get_tasks_for_date(self, date_str: str) -> List[Task]:
        """Get all tasks for a specific date"""
        tasks_data = self.data.get("tasks_data", {})
        tasks_list = tasks_data.get(date_str, [])
        return [Task.from_dict(t) for t in tasks_list]
    
    def save_tasks_for_date(self, date_str: str, tasks: List[Task]):
        """Save tasks for a specific date"""
        if "tasks_data" not in self.data:
            self.data["tasks_data"] = {}
        self.data["tasks_data"][date_str] = [t.to_dict() for t in tasks]
        self.save()
    
    def get_all_dates(self) -> List[str]:
        """Get all dates with task data, sorted"""
        return sorted(self.data.get("tasks_data", {}).keys())
    
    def get_metadata(self, key: str, default=None):
        """Get a metadata value"""
        return self.data.get("metadata", {}).get(key, default)
    
    def set_metadata(self, key: str, value):
        """Set a metadata value"""
        if "metadata" not in self.data:
            self.data["metadata"] = {}
        self.data["metadata"][key] = value
        self.save()
    
    def get_date_range_data(self, start_date: str, end_date: str) -> Dict[str, Tuple[int, int]]:
        """Get completion stats for a date range"""
        result = {}
        all_dates = self.get_all_dates()
        for date_str in all_dates:
            if start_date <= date_str <= end_date:
                tasks = self.get_tasks_for_date(date_str)
                daily = DailyTaskData(date_str, tasks)
                result[date_str] = daily.get_completion_stats()
        return result
