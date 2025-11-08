# QueueCTL - A Feature-Rich Background Job Queue System

`queuectl` is a minimal, production-grade background job queue system built in Python. It allows users to enqueue shell commands as jobs, which are then executed by one or more concurrent workers.

The system is designed to be resilient, observable, and highly controllable, featuring a rich set of bonus features including job priorities, scheduled execution, timeouts, logging, metrics, and a real-time web monitoring dashboard.

## Features

-   **Core Functionality:**
    -   **Persistent Queue**: Job data is saved in a `jobs_database.json` file, ensuring no data is lost on restart.
    -   **Multiple Worker Support**: Process jobs concurrently with multiple worker threads for high throughput.
    -   **Automatic Retry with Exponential Backoff**: Failed jobs are automatically retried with a configurable delay.
    -   **Dead Letter Queue (DLQ)**: Jobs that exhaust all retries are moved to a DLQ for manual inspection.

-   **Bonus Features Implemented**
    -   **Job Priority Queues**: Assign a priority to jobs; workers will always process higher-priority jobs first.
    -   **Scheduled/Delayed Jobs (`run_at`)**: Schedule jobs to run at a specific time in the future.
    -   **Job Timeout Handling**: Automatically fail jobs that run longer than their specified timeout.
    -   **Job Output Logging**: Capture and store the `stdout` and `stderr` of every job to a dedicated log file.
    -   **Metrics & Execution Stats**: A `metrics` command to display system throughput, success rate, and average job duration.
    -   **Minimal Web Dashboard**: A real-time, auto-refreshing web dashboard to monitor the state of all queues and jobs.

---

## Architecture Overview

The system is designed with a clear separation of concerns, making it robust and maintainable.

1.  **CLI (`cli.py`)**: The user-facing interface built with `click`. It translates user commands (`enqueue`, `logs`, `dashboard`, etc.) into actions performed by the Job Manager.

2.  **Job Management (`job.py`)**: The "brain" of the system. The `JobManager` class handles the entire job lifecycle and understands the advanced rules for priority, scheduling, and metrics calculation.

3.  **Worker Logic (`worker.py`)**: The "muscle" of the system. Each worker runs in a separate thread and is responsible for executing jobs, enforcing timeouts, and capturing output for logging.

4.  **Persistence & Concurrency (`db.py`)**: The "memory" and "traffic controller". It uses `TinyDB` for storage and a global `threading.Lock` to ensure all database operations are thread-safe, preventing file corruption and race conditions.

5.  **Web Dashboard (`dashboard.py`)**: A lightweight Flask application that provides a real-time, read-only view of the queue's state. It uses the same database lock to safely read data without interfering with the workers.

---

## Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Codemaster777/QueueCTL-BSG
    cd QueueCTL-BSG
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate on Windows
    .\venv\Scripts\activate

    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    This will install `click`, `tinydb`, and `Flask`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the CLI in Editable Mode**
    This makes the `queuectl` command available and reflects your code changes instantly.
    ```bash
    pip install --editable .
    ```

---

## Usage Examples

### 1. Check System Status
To check the status of the system:
```powershell
queuectl status
```

#### 2. Enqueue Job
The job data is a JSON string. On Windows, this must be wrapped in double quotes with inner quotes escaped.

```powershell
# Enqueue two jobs.

# The first one is a simple echo command that will succeed. 
queuectl enqueue "{\"id\":\"job-success\",\"command\":\"echo This job was a success!\"}"

# The second is a command that doesn't exist, which will fail.
queuectl enqueue "{\"id\":\"job-fail\",\"command\":\"badcommand\"}"

# Additional Advanced Jobs Examples:

# Enqueue a high-priority job with a 60-second timeout
queuectl enqueue "{\"id\":\"important_job\",\"command\":\"python process_report.py\",\"priority\":1,\"timeout\":60}"

# Enqueue a job to run 5 minutes from now
queuectl enqueue "{\"id\":\"scheduled_job\",\"command\":\"echo Task done\",\"run_at\":\"2025-11-08T14:00:00Z\"}"
```

#### 3. Start Workers
```powershell
queuectl worker start --count 2
```

#### 4. Monitor with the Dashboard
```powershell
queuectl dashboard
```
Now, open your web browser to `http://127.0.0.1:5000`. The page will auto-refresh every 5 seconds.

#### 5. Check Logs and Metrics

```powershell
# View the full output of a specific job
queuectl logs important_job

# Get a performance overview of the system
queuectl metrics
```

---

## Testing Instructions

A comprehensive validation script is included to demonstrate all core and bonus features working together. It tests job processing, priority, scheduling, timeouts, logging, and metrics.

From the project root directory, run:
```bash
python tests/TestScript.py
```
Observe the output to see the different job types being processed according to their rules.

---

## Demo:
https://drive.google.com/file/d/1gx5xLVNQYXDw2ZKMlmBkPWq8JS5qTklG/view?usp=sharing

