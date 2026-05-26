from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date, datetime
import os
import json
import io
import base64

# Configure Matplotlib backend before importing
os.environ['MPLBACKEND'] = 'Agg'
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt

# Import new modular services
from models import DataStore, Task
from services import ProductivityAnalytics
from feedback import generate_dashboard_feedback
from charts import generate_chart_data

app = Flask(__name__)

# Use Render's persistent disk path if available, otherwise local data.json
DATA_FILE = os.environ.get('DATA_FILE_PATH') or os.path.join(os.path.dirname(__file__), 'data.json')

# Initialize data store and services
data_store = DataStore(DATA_FILE)
analytics = ProductivityAnalytics(data_store)

tasks_data = data_store.data.get('tasks_data', {})


def save_data(tasks_data):
    data_store.data['tasks_data'] = tasks_data
    data_store.save()


def create_progress_chart(done_tasks, total_tasks, title):
    percentage = round((done_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(['Completed', 'Remaining'], [done_tasks, total_tasks - done_tasks], color=['#2ecc71', '#e74c3c'])
    ax.set_ylim(0, max(total_tasks, 1))
    ax.set_title(f"{title} ({percentage}% complete)")
    ax.set_ylabel('Tasks')

    for index, value in enumerate([done_tasks, total_tasks - done_tasks]):
        ax.text(index, value + 0.1, str(value), ha='center', va='bottom', fontsize=10)

    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def aggregate_monthly_stats(tasks_data):
    monthly = {}
    for date_key, task_list in tasks_data.items():
        month_key = date_key[:7]  # YYYY-MM
        done = sum(1 for item in task_list if item.get('done'))
        total = len(task_list)
        if month_key not in monthly:
            monthly[month_key] = [0, 0]
        monthly[month_key][0] += done
        monthly[month_key][1] += total
    return dict(sorted((key, tuple(value)) for key, value in monthly.items()))


@app.route('/', methods=['GET', 'POST'])
def index():
    global tasks_data
    today_str = date.today().strftime('%Y-%m-%d')
    tasks_data = data_store.data.get('tasks_data', {})

    if request.method == 'POST':
        num_tasks = int(request.form['num_tasks'])
        task_names = [request.form.get(f'task_{i}') for i in range(num_tasks)]
        tasks_data[today_str] = [{'name': t, 'done': False} for t in task_names if t]
        save_data(tasks_data)
        return redirect(url_for('index'))

    today_tasks = tasks_data.get(today_str, [])
    done_tasks = sum(1 for t in today_tasks if t['done'])
    total_tasks = len(today_tasks)

    monthly_stats = aggregate_monthly_stats(tasks_data)

    today_chart = None
    if total_tasks > 0:
        today_chart = create_progress_chart(done_tasks, total_tasks, "Today's Progress")

    if monthly_stats:
        days = sorted(monthly_stats.keys())
        done_list = [monthly_stats[d][0] for d in days]
        total_list = [monthly_stats[d][1] for d in days]

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(days, done_list, marker='o', label='Done')
        ax.plot(days, total_list, marker='o', label='Total')
        ax.set_ylabel('Tasks')
        ax.set_title('Monthly Progress')
        ax.legend()
        ax.set_xticks(days)
        ax.set_xticklabels(days, rotation=45, ha='right')

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        plt.close(fig)
        buffer.seek(0)
        monthly_chart = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    else:
        monthly_chart = None

    return render_template(
        'index.html',
        today_str=today_str,
        today_tasks=today_tasks,
        today_chart=today_chart,
        monthly_chart=monthly_chart
    )


@app.route('/mark_done/<task_date>/<int:task_index>')
def mark_done(task_date, task_index):
    global tasks_data
    tasks_data = data_store.data.get('tasks_data', {})
    if task_date in tasks_data and 0 <= task_index < len(tasks_data[task_date]):
        tasks_data[task_date][task_index]['done'] = True
        save_data(tasks_data)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
