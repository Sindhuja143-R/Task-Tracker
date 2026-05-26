"""
Smart Feedback System
Generates contextual, intelligent productivity feedback
"""

from typing import List, Dict, Optional
from services import ProductivityAnalytics
from models import DataStore


class FeedbackEngine:
    """Generates intelligent, contextual productivity feedback"""
    
    def __init__(self, analytics: ProductivityAnalytics):
        self.analytics = analytics
    
    def get_daily_feedback(self) -> List[Dict]:
        """Generate feedback for today's performance"""
        feedback_items = []
        stats = self.analytics.get_summary_stats()
        completion_rate = self.analytics.get_completion_rate(days=1)
        
        # Completion-based feedback
        if completion_rate >= 90:
            feedback_items.append({
                "type": "success",
                "message": f"Excellent. {completion_rate:.0f}% of planned tasks completed.",
                "icon": "✓"
            })
        elif completion_rate >= 75:
            feedback_items.append({
                "type": "success",
                "message": f"Good progress. {completion_rate:.0f}% completion rate.",
                "icon": "✓"
            })
        elif completion_rate >= 50:
            feedback_items.append({
                "type": "neutral",
                "message": f"On track. {completion_rate:.0f}% of tasks completed.",
                "icon": "—"
            })
        else:
            feedback_items.append({
                "type": "warning",
                "message": f"Only {completion_rate:.0f}% of tasks completed today.",
                "icon": "!"
            })
        
        # Streak-based feedback
        if stats["current_streak"] >= 5:
            feedback_items.append({
                "type": "success",
                "message": f"🔥 {stats['current_streak']} day streak maintained.",
                "icon": "🔥"
            })
        elif stats["current_streak"] >= 3:
            feedback_items.append({
                "type": "success",
                "message": f"Streak active: {stats['current_streak']} consecutive days.",
                "icon": "→"
            })
        
        return feedback_items
    
    def get_weekly_insights(self) -> List[Dict]:
        """Generate weekly performance insights"""
        insights = []
        weekly = self.analytics.get_weekly_consistency(weeks=1)
        most_productive = self.analytics.get_most_productive_day(days=7)
        
        # Consistency insight
        if weekly["score"] >= 80:
            insights.append({
                "type": "positive",
                "title": "Strong Weekly Consistency",
                "message": f"Active {weekly['days_active']} days with {weekly['avg_completion']:.0f}% avg completion.",
                "icon": "📊"
            })
        elif weekly["score"] >= 60:
            insights.append({
                "type": "neutral",
                "title": "Moderate Weekly Activity",
                "message": f"Logged {weekly['days_active']}/7 days. Try maintaining daily streaks.",
                "icon": "📅"
            })
        else:
            insights.append({
                "type": "suggestion",
                "title": "Inconsistent Weekly Pattern",
                "message": f"Only {weekly['days_active']}/7 days active. Build a daily routine.",
                "icon": "⏱️"
            })
        
        # Most productive day
        if most_productive:
            day_name = most_productive["day_name"]
            rate = most_productive["completion_rate"]
            insights.append({
                "type": "info",
                "title": f"Most Productive Day",
                "message": f"{day_name}s are your peak with {rate:.0f}% completion.",
                "icon": "⭐"
            })
        
        return insights
    
    def get_category_insights(self) -> List[Dict]:
        """Generate insights about category performance"""
        insights = []
        completion_by_category = self.analytics.get_category_completion_rate()
        distribution = self.analytics.get_category_distribution()
        
        if not completion_by_category:
            return insights
        
        # Best performing category
        best_cat = max(completion_by_category.items(), key=lambda x: x[1])
        if best_cat[1] >= 80:
            insights.append({
                "type": "positive",
                "title": f"Strong in {best_cat[0]}",
                "message": f"{best_cat[0]} tasks: {best_cat[1]:.0f}% completion rate",
                "icon": "✓"
            })
        
        # Struggling category
        if len(completion_by_category) > 1:
            worst_cat = min(completion_by_category.items(), key=lambda x: x[1])
            if worst_cat[1] < 50:
                insights.append({
                    "type": "suggestion",
                    "title": f"Focus on {worst_cat[0]}",
                    "message": f"{worst_cat[0]} has {worst_cat[1]:.0f}% completion. Consider breaking tasks into smaller steps.",
                    "icon": "⚡"
                })
        
        return insights
    
    def get_procrastination_alerts(self) -> List[Dict]:
        """Detect and alert about procrastination patterns"""
        alerts = []
        
        # Frequently postponed tasks
        postponed = self.analytics.get_frequently_postponed_tasks(min_postpones=2)
        if postponed:
            for task in postponed[:3]:  # Top 3
                alerts.append({
                    "type": "warning",
                    "title": f"Recurring Task: {task['name']}",
                    "message": f"Postponed {task['postponed_count']} times. Consider breaking it down or scheduling it.",
                    "icon": "⏰"
                })
        
        # Declining productivity
        if self.analytics.detect_productivity_decline(weeks=2):
            alerts.append({
                "type": "warning",
                "title": "Productivity Declining",
                "message": "Completion rates are decreasing. Take a break and reset your focus.",
                "icon": "📉"
            })
        
        return alerts
    
    def get_actionable_suggestions(self) -> List[str]:
        """Generate actionable suggestions for improvement"""
        suggestions = []
        
        stats = self.analytics.get_summary_stats()
        weekly = self.analytics.get_weekly_consistency(weeks=1)
        
        # Streak suggestion
        if stats["current_streak"] == 0:
            suggestions.append("Start a new streak by completing today's tasks.")
        elif stats["current_streak"] < 7:
            suggestions.append(f"You're {7 - stats['current_streak']} days away from a weekly streak.")
        
        # Consistency suggestion
        if weekly["days_active"] < 5:
            suggestions.append("Try to log tasks every day for better consistency tracking.")
        
        # Category focus
        completion_by_category = self.analytics.get_category_completion_rate()
        if completion_by_category:
            worst = min(completion_by_category.items(), key=lambda x: x[1])
            if worst[1] < 60:
                suggestions.append(f"Prioritize {worst[0]} tasks earlier in the day.")
        
        # Postponement
        postponed = self.analytics.get_frequently_postponed_tasks(min_postpones=2)
        if postponed:
            suggestions.append(f"Address '{postponed[0]['name']}' today before it gets postponed again.")
        
        return suggestions[:3]  # Top 3 suggestions
    
    def get_motivational_context(self) -> Dict:
        """Get contextual motivational info (not cheesy quotes)"""
        stats = self.analytics.get_summary_stats()
        completion_rate = self.analytics.get_completion_rate(days=30)
        
        context = {
            "streak": stats["current_streak"],
            "consistency": stats["weekly_consistency"],
            "completion_rate": completion_rate,
            "trend": "improving" if not stats["is_declining"] else "needs attention"
        }
        
        # Generate contextual status message
        if stats["current_streak"] >= 7 and completion_rate >= 80:
            context["status"] = "You've built strong momentum. Maintain it."
        elif stats["current_streak"] >= 3:
            context["status"] = "Good consistency. Push to extend your streak."
        elif completion_rate >= 75:
            context["status"] = "Strong performance. Aim for daily consistency."
        else:
            context["status"] = "Start with today. Build from there."
        
        return context


def generate_dashboard_feedback(analytics: ProductivityAnalytics) -> Dict:
    """
    Generate all feedback for the dashboard
    Used by Flask routes to populate the dashboard
    """
    engine = FeedbackEngine(analytics)
    
    return {
        "daily_feedback": engine.get_daily_feedback(),
        "weekly_insights": engine.get_weekly_insights(),
        "category_insights": engine.get_category_insights(),
        "procrastination_alerts": engine.get_procrastination_alerts(),
        "suggestions": engine.get_actionable_suggestions(),
        "motivational": engine.get_motivational_context()
    }
