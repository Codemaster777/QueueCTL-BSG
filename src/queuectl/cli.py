# cli.py - THE MAIN ENTRY POINT FOR ALL CLI COMMANDS (WITH DESCRIPTIONS)
import click
import json
from .job import JobManager
from .worker import StartWorkers, StopWorkers
from .db import GetDbConnection, JobQuery, DatabaseLock
from .config import SetConfigValue
from .dashboard import RunDashboard
import os

# COMMANDS DEFINITION
@click.group()
def MainCLI():
    """A CLI for managing a robust, file-based background job queue."""
    pass

@MainCLI.command()
@click.argument('job_data')
def enqueue(job_data):
    """Add a new job to the queue."""
    newJob = JobManager.CreateJob(job_data)
    click.echo(f"Enqueued job {newJob['id']}.")

@click.group()
def worker():
    """Manage worker processes."""
    pass


@worker.command()
@click.option('--count', default=1, help='Number of workers to start.')
def start(count):
    """Start one or more worker processes."""
    workerThreads = StartWorkers(count)
    click.echo(f"Started {count} worker(s). Press Ctrl+C to stop.")
    try:
        for aThread in workerThreads:
            aThread.join()
    except KeyboardInterrupt:
        click.echo("\nGRACEFULLY SHUTTING DOWN WORKERS...")
        StopWorkers()
        for aThread in workerThreads:
            aThread.join()
        click.echo("ALL WORKERS HAVE STOPPED.")
MainCLI.add_command(worker)


@MainCLI.command()
def status():
    """Show a summary of job states."""
    with DatabaseLock:
        db = GetDbConnection()
        JobsTable = db.table('Jobs')
        DlqTable = db.table('DLQ')
        pendingCount = JobsTable.count(JobQuery.state == 'pending')
        processingCount = JobsTable.count(JobQuery.state == 'processing')
        completedCount = JobsTable.count(JobQuery.state == 'completed')
        failedCount = JobsTable.count(JobQuery.state == 'failed')
        deadCount = len(DlqTable)
        db.close()
    click.echo(f"Pending: {pendingCount}, Processing: {processingCount}, Completed: {completedCount}, Failed: {failedCount}, DLQ: {deadCount}")

@MainCLI.command('list')
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed']), help='Filter jobs by state.')
def ListJobs(state):
    """List jobs, optionally filtering by state."""
    with DatabaseLock:
        db = GetDbConnection()
        JobsTable = db.table('Jobs')
        if state:
            jobs = JobsTable.search(JobQuery.state == state)
        else:
            jobs = JobsTable.all()
        db.close()
    click.echo(json.dumps(jobs, indent=2))


@click.group()
def dlq():
    """Manage the Dead Letter Queue."""
    pass

@dlq.command('list')
def ListDlq():
    """List all jobs in the DLQ."""
    with DatabaseLock:
        db = GetDbConnection()
        DlqTable = db.table('DLQ')
        dlqJobs = DlqTable.all()
        db.close()
    click.echo(json.dumps(dlqJobs, indent=2))

@dlq.command()
@click.argument('job_id')
def retry(job_id):
    """Retry a job from the DLQ."""
    with DatabaseLock:
        db = GetDbConnection()
        JobsTable = db.table('Jobs')
        DlqTable = db.table('DLQ')
        jobToRetry = DlqTable.get(JobQuery.id == job_id)
        if jobToRetry:
            DlqTable.remove(JobQuery.id == job_id)
            jobToRetry['state'] = 'pending'
            jobToRetry['attempts'] = 0
            JobsTable.insert(jobToRetry)
            click.echo(f"Job {job_id} has been moved back to the queue for retry.")
        else:
            click.echo(f"Error: Job {job_id} not found in DLQ.", err=True)
        db.close()
MainCLI.add_command(dlq)


@click.group()
def config():
    """Manage system configuration."""
    pass

@config.command()
@click.argument('key', type=click.Choice(['max-retries', 'backoff-base']))
@click.argument('value', type=int)
def set(key, value):
    """Set a configuration value."""
    dbKey = 'maxRetries' if key == 'max-retries' else 'backoffBase'
    SetConfigValue(dbKey, value)
    click.echo(f"Configuration updated: {key} = {value}")
MainCLI.add_command(config)

# BONUS COMMANDS

@MainCLI.command()
@click.argument('job_id')
def logs(job_id):
    """Display the log file for a given job ID."""
    log_file = f"logs/{job_id}.log"
    if not os.path.exists(log_file):
        click.echo(f"Error: Log file not found for job {job_id}.", err=True)
        return
    with open(log_file, 'r') as f:
        click.echo(f.read())

@MainCLI.command()
def metrics():
    """Show execution stats for completed and dead jobs."""
    with DatabaseLock:
        db = GetDbConnection()
        JobsTable = db.table('Jobs')
        DlqTable = db.table('DLQ')
        completed_jobs = JobsTable.search(JobQuery.state == 'completed')
        dead_jobs = DlqTable.all()
        db.close()

    total_finished = len(completed_jobs) + len(dead_jobs)
    if total_finished == 0:
        click.echo("No jobs have finished yet.")
        return

    total_duration = sum(j.get('duration_seconds', 0) for j in completed_jobs + dead_jobs if j.get('duration_seconds'))
    avg_duration = total_duration / total_finished if total_finished > 0 else 0
    success_rate = (len(completed_jobs) / total_finished) * 100 if total_finished > 0 else 0

    click.echo("Execution Metrics")
    click.echo(f"Total Jobs Finished: {total_finished}")
    click.echo(f"  - Completed: {len(completed_jobs)}")
    click.echo(f"  - Dead: {len(dead_jobs)}")
    click.echo(f"Success Rate: {success_rate:.2f}%")
    click.echo(f"Average Job Duration: {avg_duration:.2f} seconds")

@MainCLI.command()
def dashboard():
    """Launch a minimal web dashboard for monitoring."""
    click.echo("Starting web dashboard at http://127.0.0.1:5000/")
    click.echo("Press Ctrl+C to stop the dashboard.")
    RunDashboard()











