"""
Analytics Service for Productivity Intelligence
Calculates metrics, streaks, trends, and insights
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from models import DataStore, Task


class ProductivityAnalytics:
    """Core analytics engine for productivity metrics"""
    
    def __init__(self, data_store: DataStore):
        self.ds = data_store
    
    def get_completion_rate(self, days: int = 30) -> float:
        """Calculate completion rate for last N days"""
        dates = self.ds.get_all_dates()
        if not dates:
            return 0.0
        
        # Filter to last N days
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        relevant_dates = [d for d in dates if d >= cutoff_date]
        
        if not relevant_dates:
            return 0.0
        
        total_done = 0
        total_tasks = 0
        
        for date_str in relevant_dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            done = sum(1 for t in tasks if t.done)
            total_done += done
            total_tasks += len(tasks)
        
        if total_tasks == 0:
            return 0.0
        
        return (total_done / total_tasks) * 100
    
    def get_current_streak(self) -> Tuple[int, str]:
        """
        Calculate current streak (consecutive days with >80% completion)
        Returns (streak_count, end_date)
        """
        dates = sorted(self.ds.get_all_dates(), reverse=True)
        streak = 0
        
        for date_str in dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            if not tasks:
                break
            
            completed = sum(1 for t in tasks if t.done)
            completion_rate = (completed / len(tasks)) * 100 if tasks else 0
            
            if completion_rate >= 80:
                streak += 1
            else:
                break
        
        latest_date = dates[0] if dates else "N/A"
        return streak, latest_date
    
    def get_weekly_consistency(self, weeks: int = 1) -> Dict:
        """Calculate weekly consistency metrics"""
        dates = self.ds.get_all_dates()
        if not dates:
            return {"score": 0, "days_active": 0, "avg_completion": 0}
        
        # Get dates from last N weeks
        cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        relevant_dates = [d for d in dates if d >= cutoff_date]
        
        if not relevant_dates:
            return {"score": 0, "days_active": 0, "avg_completion": 0}
        
        days_active = len(relevant_dates)
        days_in_period = 7 * weeks
        
        total_completion = 0
        for date_str in relevant_dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            if tasks:
                completed = sum(1 for t in tasks if t.done)
                total_completion += (completed / len(tasks)) * 100
        
        avg_completion = total_completion / len(relevant_dates) if relevant_dates else 0
        consistency_score = (days_active / days_in_period) * 100
        
        return {
            "score": round(consistency_score, 1),
            "days_active": days_active,
            "avg_completion": round(avg_completion, 1)
        }
    
    def get_most_productive_day(self, days: int = 30) -> Optional[Dict]:
        """Find the most productive day in last N days"""
        dates = self.ds.get_all_dates()
        if not dates:
            return None
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        relevant_dates = [d for d in dates if d >= cutoff_date]
        
        if not relevant_dates:
            return None
        
        best_rate = 0
        best_date = None
        
        for date_str in relevant_dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            if tasks:
                completed = sum(1 for t in tasks if t.done)
                rate = (completed / len(tasks)) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_date = date_str
        
        if best_date:
            return {
                "date": best_date,
                "completion_rate": round(best_rate, 1),
                "day_name": datetime.strptime(best_date, "%Y-%m-%d").strftime("%A")
            }
        return None
    
    def get_category_distribution(self, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, int]:
        """Get task count by category"""
        dates = self.ds.get_all_dates()
        
        if date_range:
            dates = [d for d in dates if date_range[0] <= d <= date_range[1]]
        
        categories = {}
        
        for date_str in dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            for task in tasks:
                category = task.category or "Personal"
                categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def get_category_completion_rate(self, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, float]:
        """Get completion rate by category"""
        dates = self.ds.get_all_dates()
        
        if date_range:
            dates = [d for d in dates if date_range[0] <= d <= date_range[1]]
        
        stats = {}
        
        for date_str in dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            for task in tasks:
                category = task.category or "Personal"
                if category not in stats:
                    stats[category] = {"done": 0, "total": 0}
                
                stats[category]["total"] += 1
                if task.done:
                    stats[category]["done"] += 1
        
        # Calculate rates
        result = {}
        for category, counts in stats.items():
            rate = (counts["done"] / counts["total"] * 100) if counts["total"] > 0 else 0
            result[category] = round(rate, 1)
        
        return result
    
    def get_frequently_postponed_tasks(self, min_postpones: int = 2) -> List[Dict]:
        """Find tasks that are frequently postponed"""
        dates = self.ds.get_all_dates()
        task_stats = {}
        
        for date_str in dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            for task in tasks:
                if task.postponed_count >= min_postpones:
                    key = task.name
                    if key not in task_stats:
                        task_stats[key] = {
                            "name": task.name,
                            "category": task.category,
                            "postponed_count": task.postponed_count,
                            "done": task.done
                        }
        
        return sorted(task_stats.values(), key=lambda x: x["postponed_count"], reverse=True)
    
    def detect_productivity_decline(self, weeks: int = 4) -> bool:
        """Detect if productivity is declining"""
        dates = sorted(self.ds.get_all_dates())
        if len(dates) < 14:  # Need at least 2 weeks
            return False
        
        cutoff = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        relevant = [d for d in dates if d >= cutoff]
        
        if len(relevant) < 14:
            return False
        
        # Split into two halves
        mid = len(relevant) // 2
        first_half = relevant[:mid]
        second_half = relevant[mid:]
        
        # Calculate average completion rate for each half
        first_avg = self._calculate_period_average(first_half)
        second_avg = self._calculate_period_average(second_half)
        
        # Decline if second half is 15%+ lower
        return (first_avg - second_avg) > 15
    
    def _calculate_period_average(self, dates: List[str]) -> float:
        """Helper to calculate average completion rate for a list of dates"""
        if not dates:
            return 0.0
        
        total = 0
        for date_str in dates:
            tasks = self.ds.get_tasks_for_date(date_str)
            if tasks:
                completed = sum(1 for t in tasks if t.done)
                total += (completed / len(tasks)) * 100
        
        return total / len(dates) if dates else 0.0
    
    def get_daily_completion_trend(self, days: int = 30) -> List[Dict]:
        """Get daily completion rates for trend analysis"""
        dates = self.ds.get_all_dates()
        if not dates:
            return []
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        relevant = [d for d in dates if d >= cutoff]
        
        result = []
        for date_str in sorted(relevant):
            tasks = self.ds.get_tasks_for_date(date_str)
            if tasks:
                completed = sum(1 for t in tasks if t.done)
                rate = (completed / len(tasks)) * 100
                result.append({
                    "date": date_str,
                    "completion_rate": round(rate, 1),
                    "completed": completed,
                    "total": len(tasks)
                })
        
        return result
    
    def get_summary_stats(self) -> Dict:
        """Get comprehensive summary statistics"""
        streak, streak_date = self.get_current_streak()
        weekly = self.get_weekly_consistency(weeks=1)
        most_productive = self.get_most_productive_day(days=30)
        completion_rate = self.get_completion_rate(days=30)
        
        return {
            "current_streak": streak,
            "streak_end_date": streak_date,
            "weekly_consistency": weekly["score"],
            "completion_rate_30d": round(completion_rate, 1),
            "days_active_week": weekly["days_active"],
            "most_productive_day": most_productive,
            "is_declining": self.detect_productivity_decline(weeks=4)
        }
