# job.py - MANAGES THE JOB LIFECYCLE (UPGRADED WITH BONUS FEATURES)
import uuid
import json
from datetime import datetime, timezone
from .db import GetDbConnection, JobQuery, DatabaseLock
from .config import GetConfigValue

class JobManager:
    @staticmethod
    def CreateJob(jobDataString):
        with DatabaseLock:
            db = GetDbConnection()
            JobsTable = db.table('Jobs')
            parsedData = json.loads(jobDataString)
            now = datetime.now(timezone.utc)
            run_at_str = parsedData.get('run_at', now.isoformat())
            run_at_dt = datetime.fromisoformat(run_at_str.replace('Z', '+00:00'))

            newJob = {
                "id": parsedData.get('id', str(uuid.uuid4())),
                "command": parsedData['command'],
                "state": "pending",
                "attempts": 0,
                "max_retries": GetConfigValue('maxRetries'),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                # BONUS FEATURE FIELDS
                "priority": int(parsedData.get('priority', 10)), # LOWER IS HIGHER PRIORITY
                "timeout": int(parsedData.get('timeout', 300)), #  5 MIN DEFAULT
                "run_at": run_at_dt.isoformat(),
                "log_file": f"logs/{parsedData.get('id', 'unassigned_id')}.log",
                "started_at": None,
                "finished_at": None,
                "duration_seconds": None,
                "output": None,
            }
            JobsTable.insert(newJob)
            db.close()
            return newJob

    @staticmethod
    def FindAndLockPending():
        with DatabaseLock:
            db = GetDbConnection()
            JobsTable = db.table('Jobs')
            now = datetime.now(timezone.utc)

            # FETCH CANDIDATE JOBS THAT ARE DUE TO RUN
            candidates = JobsTable.search(
                (JobQuery.state == 'pending') &
                (JobQuery.run_at <= now.isoformat())
            )

            if not candidates:
                db.close()
                return None

            # SORT CANDIDATES BY PRIORITY AND CREATED_AT
            candidates.sort(key=lambda j: (j.get('priority', 10), j['created_at']))
            
            bestJob = candidates[0]

            # LOCK THE JOB BY UPDATING ITS STATE TO 'PROCESSING'
            updates = {
                'state': 'processing',
                'updated_at': now.isoformat(),
                'started_at': now.isoformat()
            }
            JobsTable.update(updates, doc_ids=[bestJob.doc_id])
            bestJob.update(updates)

            db.close()
            return bestJob


    @staticmethod
    def UpdateJob(jobId, updates):
        with DatabaseLock:
            db = GetDbConnection()
            JobsTable = db.table('Jobs')
            
            # UPDATING METRICS IF JOB IS COMPLETED, FAILED, OR DEAD
            if updates.get('state') in ['completed', 'failed', 'dead']:
                job = JobsTable.get(JobQuery.id == jobId) 
                if job and job.get('started_at'):
                    started = datetime.fromisoformat(job['started_at'])
                    finished = datetime.now(timezone.utc)
                    updates['finished_at'] = finished.isoformat()
                    updates['duration_seconds'] = round((finished - started).total_seconds(), 2)

            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            JobsTable.update(updates, JobQuery.id == jobId)
            db.close()

    @staticmethod
    def MoveToDlq(failedJob):
        with DatabaseLock:
            db = GetDbConnection()
            JobsTable = db.table('Jobs')
            DlqTable = db.table('DLQ')
            
            # FINALIZING METRICS BEFORE MOVING TO DLQ
            started = datetime.fromisoformat(failedJob['started_at']) if failedJob.get('started_at') else datetime.now(timezone.utc)
            finished = datetime.now(timezone.utc)
            failedJob['state'] = 'dead'
            failedJob['updated_at'] = finished.isoformat()
            failedJob['finished_at'] = finished.isoformat()
            failedJob['duration_seconds'] = (finished - started).total_seconds()

            DlqTable.insert(failedJob)
            JobsTable.remove(JobQuery.id == failedJob['id'])
            db.close()