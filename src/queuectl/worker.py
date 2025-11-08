# worker.py - DEFINES WORKER LOGIC FOR PROCESSING JOBS (UPGRADED WITH BONUS FEATURES)
import time
import subprocess
import threading
import os
from .job import JobManager
from .config import GetConfigValue

StopEventFlag = threading.Event()

def EnsureLogDirectory():
    """Ensures the 'logs' directory exists."""
    os.makedirs('logs', exist_ok=True)

def RunWorkerLoop(workerId):
    EnsureLogDirectory()
    print(f"WORKER {workerId} STARTED.")
    while not StopEventFlag.is_set():
        jobToProcess = JobManager.FindAndLockPending()
        if jobToProcess:
            print(f"WORKER {workerId} PICKED UP JOB {jobToProcess['id']}.")
            ExecuteJob(jobToProcess)
        else:
            time.sleep(1)
    print(f"WORKER {workerId} STOPPING.")

def ExecuteJob(currentJob):
    updates = {}
    try:
        timeout = currentJob.get('timeout', 300)
        result = subprocess.run(
            currentJob['command'],
            shell=True,
            check=True,
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        updates['state'] = 'completed'
        updates['output'] = result.stdout[-1000:] # CAPTURE LAST 1000 CHARACTERS
        print(f"JOB {currentJob['id']} SUCCEEDED.")
    except subprocess.CalledProcessError as error:
        updates['state'] = 'failed'
        updates['output'] = error.stderr[-1000:]
        print(f"JOB {currentJob['id']} FAILED: {error}")
    except subprocess.TimeoutExpired as terror:
        updates['state'] = 'failed'
        updates['output'] = f"Job timed out after {terror.timeout} seconds."
        print(f"JOB {currentJob['id']} FAILED: TIMEOUT")
    except Exception as e:
        updates['state'] = 'failed'
        updates['output'] = f"An unexpected error occurred: {str(e)}"
        print(f"JOB {currentJob['id']} FAILED: UNEXPECTED ERROR")

    # WRITING LOG OUTPUT TO FILE
    full_output = updates.get('output', 'No output captured.')
    if 'result' in locals() and result:
        full_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    
    try:
        with open(currentJob['log_file'], 'w') as f:
            f.write(full_output)
    except IOError as e:
        print(f"Could not write log for job {currentJob['id']}: {e}")

    # FINALIZING JOB STATUS
    if updates.get('state') == 'completed':
        JobManager.UpdateJob(currentJob['id'], updates)
    else:
        HandleFailure(currentJob, updates)

def HandleFailure(failedJob, updates):
    newAttemptCount = failedJob['attempts'] + 1
    maxRetries = GetConfigValue('maxRetries')

    JobManager.UpdateJob(failedJob['id'], updates) 

    if newAttemptCount >= maxRetries:
        print(f"JOB {failedJob['id']} REACHED MAX RETRIES. MOVING TO DLQ.")
        JobManager.MoveToDlq(failedJob)
    else:
        backoffDelay = GetConfigValue('backoffBase') ** newAttemptCount
        print(f"JOB {failedJob['id']} WILL RETRY IN {backoffDelay} SECONDS.")
        # UPDATING ATTEMPT COUNT BEFORE SLEEPING
        JobManager.UpdateJob(failedJob['id'], {"attempts": newAttemptCount})
        time.sleep(backoffDelay)
        # RESETTING JOB STATE TO PENDING FOR RETRY
        JobManager.UpdateJob(failedJob['id'], {"state": "pending"})

def StartWorkers(workerCount):
    workerThreads = []
    for i in range(workerCount):
        aThread = threading.Thread(target=RunWorkerLoop, args=(i + 1,))
        aThread.start()
        workerThreads.append(aThread)
    return workerThreads

def StopWorkers():
    StopEventFlag.set()