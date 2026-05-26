from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import matplotlib.pyplot as plt
import io
import base64
import json
import os

app = Flask(__name__)

# Use Render's persistent disk path
DATA_FILE = "/opt/render/project/data/data.json"

# ----------------- Storage Helpers -----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}, {}
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
            return data.get("tasks_data", {}), data.get("monthly_stats", {})
        except json.JSONDecodeError:
            return {}, {}

def save_data(tasks, monthly):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump({
            "tasks_data": tasks,
            "monthly_stats": monthly
        }, f)

tasks_data, monthly_stats = load_data()

# ----------------- Chart Helper -----------------
def create_progress_chart(done, total, title):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(['Done', 'Remaining'], [done, total - done], color=['green', 'red'])
    ax.set_ylim(0, max(1, total))
    ax.set_ylabel("Tasks")
    ax.set_title(title)
    ax.bar_label(ax.containers[0])

    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{graph_url}"

# ----------------- Routes -----------------
@app.route('/', methods=['GET', 'POST'])
def index():
    global tasks_data, monthly_stats
    today_str = date.today().strftime("%Y-%m-%d")

    if request.method == 'POST':
        num_tasks = int(request.form['num_tasks'])
        task_names = [request.form.get(f'task_{i}') for i in range(num_tasks)]
        tasks_data[today_str] = [{"name": t, "done": False} for t in task_names]
        save_data(tasks_data, monthly_stats)
        return redirect(url_for('index'))

    today_tasks = tasks_data.get(today_str, [])
    done_tasks = sum(1 for t in today_tasks if t["done"])
    total_tasks = len(today_tasks)

    monthly_stats[today_str] = (done_tasks, total_tasks)
    save_data(tasks_data, monthly_stats)

    today_chart = None
    if total_tasks > 0:
        today_chart = create_progress_chart(done_tasks, total_tasks, "Today's Progress")

    if monthly_stats:
        days = sorted(monthly_stats.keys())
        done_list = [monthly_stats[d][0] for d in days]
        total_list = [monthly_stats[d][1] for d in days]

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(days, done_list, marker='o', label='Done')
        ax.plot(days, total_list, marker='o', label='Total')
        ax.set_ylabel("Tasks")
        ax.set_title("Monthly Progress")
        ax.legend()

        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        monthly_chart = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
        monthly_chart = f"data:image/png;base64,{monthly_chart}"
    else:
        monthly_chart = None

    return render_template(
        "index.html",
        today_str=today_str,
        today_tasks=today_tasks,
        today_chart=today_chart,
        monthly_chart=monthly_chart
    )

@app.route('/mark_done/<task_date>/<int:task_index>')
def mark_done(task_date, task_index):
    global tasks_data, monthly_stats
    if task_date in tasks_data and 0 <= task_index < len(tasks_data[task_date]):
        tasks_data[task_date][task_index]["done"] = True
        save_data(tasks_data, monthly_stats)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
