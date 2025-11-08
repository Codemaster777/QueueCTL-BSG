# dashboard.py - A MINIMAL FLASK WEB DASHBOARD (DEFINITIVELY CORRECTED)
from flask import Flask, render_template, abort
from .db import GetDbConnection, JobQuery, DatabaseLock
import os
import click

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

# DEFINING LOGICAL DEFAULTS FOR SORTING
# OLD TIMESTAMP: FOR DESCENDING SORTS (NEWEST FIRST).
# FUTURE TIMESTAMP: FOR ASCENDING SORTS (OLDEST FIRST).
OLDEST_TIMESTAMP = "1970-01-01T00:00:00+00:00"
NEWEST_TIMESTAMP = "9999-12-31T23:59:59+00:00"

@app.route('/')
def index():
    """
    Main route to display the dashboard. Fetches all data and renders it.
    It's wrapped in a try/except to prevent the server from crashing.
    """
    try:
        with DatabaseLock:
            db = GetDbConnection()
            JobsTable = db.table('Jobs')
            DlqTable = db.table('DLQ')
            all_jobs = JobsTable.all()
            dlq_jobs = DlqTable.all()
            db.close()
        
        # CATEGORIZE JOBS BY STATE
        pending = [j for j in all_jobs if j['state'] == 'pending']
        processing = [j for j in all_jobs if j['state'] == 'processing']
        completed = [j for j in all_jobs if j['state'] == 'completed']
        failed = [j for j in all_jobs if j['state'] == 'failed']

        # SORT JOBS WITHIN EACH CATEGORY
        pending.sort(key=lambda j: j.get('created_at', NEWEST_TIMESTAMP))
        processing.sort(key=lambda j: j.get('started_at', NEWEST_TIMESTAMP))
        completed.sort(key=lambda j: j.get('finished_at', OLDEST_TIMESTAMP), reverse=True)
        failed.sort(key=lambda j: j.get('updated_at', OLDEST_TIMESTAMP), reverse=True)
        dlq_jobs.sort(key=lambda j: j.get('updated_at', OLDEST_TIMESTAMP), reverse=True)
        
        return render_template(
            'dashboard.html',
            pending=pending,
            processing=processing,
            completed=completed,
            failed=failed,
            dlq=dlq_jobs
        )
    except Exception as e:
        abort(500, description=f"An error occurred while reading the database: {e}")


def RunDashboard():
    """
    Starts the Flask development server to run the dashboard.
    """
    click.echo("Starting web dashboard at http://127.0.0.1:5000/")
    click.echo("Press Ctrl+C to stop the dashboard.")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    RunDashboard()