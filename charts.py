"""
Chart Data Generation Utilities
Produces chart configuration data for Chart.js visualization
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from services import ProductivityAnalytics
from models import DataStore


class ChartDataGenerator:
    """Generates chart data for interactive visualizations"""
    
    def __init__(self, analytics: ProductivityAnalytics, data_store: DataStore):
        self.analytics = analytics
        self.ds = data_store
    
    def get_today_progress_chart(self) -> Dict[str, Any]:
        """Generate today's progress bar chart data"""
        today = datetime.now().strftime("%Y-%m-%d")
        tasks = self.ds.get_tasks_for_date(today)
        
        done = sum(1 for t in tasks if t.done)
        total = len(tasks)
        remaining = total - done
        
        return {
            "type": "doughnut",
            "labels": ["Completed", "Remaining"],
            "data": [done, remaining],
            "colors": ["#2ecc71", "#e74c3c"],
            "backgroundColor": ["#2ecc7133", "#e74c3c33"],
            "borderColor": ["#2ecc71", "#e74c3c"],
            "stats": {
                "completed": done,
                "total": total,
                "percentage": round((done / total * 100) if total > 0 else 0, 1)
            }
        }
    
    def get_weekly_trend_chart(self, days: int = 7) -> Dict[str, Any]:
        """Generate weekly trend line chart"""
        trend_data = self.analytics.get_daily_completion_trend(days=days)
        
        if not trend_data:
            return {"type": "line", "labels": [], "datasets": []}
        
        labels = [d["date"] for d in trend_data]
        completion_rates = [d["completion_rate"] for d in trend_data]
        
        return {
            "type": "line",
            "labels": labels,
            "datasets": [
                {
                    "label": "Completion Rate %",
                    "data": completion_rates,
                    "borderColor": "#2ecc71",
                    "backgroundColor": "#2ecc7133",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.4,
                    "pointRadius": 5,
                    "pointBackgroundColor": "#2ecc71"
                }
            ],
            "options": {
                "scales": {
                    "y": {
                        "min": 0,
                        "max": 100,
                        "ticks": {"suffix": "%"}
                    }
                }
            }
        }
    
    def get_category_distribution_chart(self) -> Dict[str, Any]:
        """Generate category pie chart"""
        distribution = self.analytics.get_category_distribution()
        
        if not distribution:
            return {"type": "pie", "labels": [], "datasets": []}
        
        # Define colors for categories
        colors = {
            "Study": "#3498db",
            "Coding": "#9b59b6",
            "Health": "#e74c3c",
            "Fitness": "#f39c12",
            "Personal": "#1abc9c",
            "Work": "#34495e",
            "UPSC": "#16a085"
        }
        
        labels = list(distribution.keys())
        data = list(distribution.values())
        chart_colors = [colors.get(label, "#95a5a6") for label in labels]
        
        return {
            "type": "pie",
            "labels": labels,
            "datasets": [
                {
                    "data": data,
                    "backgroundColor": chart_colors,
                    "borderColor": "#fff",
                    "borderWidth": 2
                }
            ]
        }
    
    def get_category_completion_chart(self) -> Dict[str, Any]:
        """Generate category completion rate bar chart"""
        completion_rates = self.analytics.get_category_completion_rate()
        
        if not completion_rates:
            return {"type": "bar", "labels": [], "datasets": []}
        
        labels = list(completion_rates.keys())
        data = list(completion_rates.values())
        
        # Color based on performance
        colors = []
        for rate in data:
            if rate >= 80:
                colors.append("#2ecc71")
            elif rate >= 60:
                colors.append("#f39c12")
            else:
                colors.append("#e74c3c")
        
        return {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {
                    "label": "Completion Rate %",
                    "data": data,
                    "backgroundColor": colors,
                    "borderRadius": 6,
                    "borderSkipped": False
                }
            ],
            "options": {
                "scales": {
                    "y": {
                        "min": 0,
                        "max": 100
                    }
                }
            }
        }
    
    def get_monthly_overview_chart(self, months: int = 1) -> Dict[str, Any]:
        """Generate monthly overview chart"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30*months)).strftime("%Y-%m-%d")
        
        range_data = self.ds.get_date_range_data(start_date, end_date)
        
        if not range_data:
            return {"type": "bar", "labels": [], "datasets": []}
        
        dates = sorted(range_data.keys())
        completed = [range_data[d][0] for d in dates]
        total = [range_data[d][1] for d in dates]
        
        return {
            "type": "bar",
            "labels": dates,
            "datasets": [
                {
                    "label": "Completed",
                    "data": completed,
                    "backgroundColor": "#2ecc71",
                    "borderRadius": 4
                },
                {
                    "label": "Total",
                    "data": total,
                    "backgroundColor": "#3498db",
                    "borderRadius": 4
                }
            ]
        }
    
    def get_weekly_heatmap_data(self) -> Dict[str, Any]:
        """Generate data for weekly heatmap (day of week performance)"""
        dates = self.ds.get_all_dates()
        
        # Map days: 0=Monday, 6=Sunday
        day_stats = {i: {"done": 0, "total": 0} for i in range(7)}
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for date_str in dates:
            day_index = datetime.strptime(date_str, "%Y-%m-%d").weekday()
            tasks = self.ds.get_tasks_for_date(date_str)
            
            done = sum(1 for t in tasks if t.done)
            total = len(tasks)
            
            day_stats[day_index]["done"] += done
            day_stats[day_index]["total"] += total
        
        # Calculate completion rate for each day
        completion_rates = []
        for i in range(7):
            stat = day_stats[i]
            if stat["total"] > 0:
                rate = (stat["done"] / stat["total"]) * 100
            else:
                rate = 0
            completion_rates.append(round(rate, 1))
        
        # Color based on performance
        colors = []
        for rate in completion_rates:
            if rate >= 80:
                colors.append("#2ecc71")
            elif rate >= 60:
                colors.append("#f39c12")
            else:
                colors.append("#e74c3c")
        
        return {
            "type": "bar",
            "title": "Weekly Pattern (All Time)",
            "labels": day_names,
            "data": completion_rates,
            "colors": colors,
            "backgroundColor": colors,
            "message": "Your productivity pattern by day of week"
        }
    
    def get_streak_data(self) -> Dict[str, Any]:
        """Generate streak visualization data"""
        streak, streak_date = self.analytics.get_current_streak()
        
        return {
            "type": "metric",
            "value": streak,
            "label": "Day Streak",
            "end_date": streak_date,
            "icon": "🔥" if streak > 0 else "—",
            "status": "active" if streak > 0 else "inactive"
        }
    
    def get_all_charts_data(self) -> Dict[str, Dict]:
        """Generate all chart data at once"""
        return {
            "today_progress": self.get_today_progress_chart(),
            "weekly_trend": self.get_weekly_trend_chart(),
            "category_distribution": self.get_category_distribution_chart(),
            "category_completion": self.get_category_completion_chart(),
            "monthly_overview": self.get_monthly_overview_chart(),
            "weekly_heatmap": self.get_weekly_heatmap_data(),
            "streak": self.get_streak_data()
        }


def generate_chart_data(analytics: ProductivityAnalytics, data_store: DataStore) -> Dict:
    """
    Generate all chart data for the dashboard
    Used by Flask routes to populate interactive charts
    """
    generator = ChartDataGenerator(analytics, data_store)
    return generator.get_all_charts_data()
