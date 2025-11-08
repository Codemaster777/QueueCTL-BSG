# test_flows.py - A SCRIPT TO VALIDATE ALL CORE AND BONUS FEATURES
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

def ExecuteCommand(commandString):
    print(f"\n--- RUNNING: {commandString} ---")
    try:
        subprocess.run(commandString, shell=True, check=True, text=True, timeout=30)
    except subprocess.CalledProcessError as error:
        print(f"COMMAND FAILED WITH ERROR: {error}")
    except subprocess.TimeoutExpired:
        print("COMMAND TIMED OUT!")

def RunTestProcess():
    # ENSURING A CLEAN SLATE
    if os.path.exists("jobs_database.json"):
        os.remove("jobs_database.json")
    if os.path.exists("logs"):
        for f in os.listdir('logs'):
            try:
                os.remove(os.path.join('logs', f))
            except OSError as e:
                print(f"Error removing log file {f}: {e}")
    else:
        os.makedirs('logs')

    # TEST CONFIGURATION SETTING
    print("\n--- 1. CONFIGURING SYSTEM ---")
    ExecuteCommand("queuectl config set max-retries 2")
    ExecuteCommand("queuectl config set backoff-base 1")

    # TEST JOB ENQUEUEING
    print("\n--- 2. ENQUEUEING TEST JOBS ---")
    # A. NORMAL HIGH-PRIORITY JOB
    ExecuteCommand('queuectl enqueue "{\\"id\\":\\"jobHighPriority\\",\\"command\\":\\"echo HIGH PRIORITY\\",\\"priority\\":1}"')
    # B. NORMAL JOB
    ExecuteCommand('queuectl enqueue "{\\"id\\":\\"jobSuccess\\",\\"command\\":\\"echo SUCCESS\\",\\"priority\\":5}"')
    # C. SCHEDULED JOB
    future_time = (datetime.now(timezone.utc) + timedelta(seconds=20)).isoformat() # Increased delay
    ExecuteCommand(f'queuectl enqueue "{{\\"id\\":\\"jobScheduled\\",\\"command\\":\\"echo SCHEDULED\\",\\"run_at\\":\\"{future_time}\\"}}"')
    # D. TIMEOUT JOB
    ExecuteCommand('queuectl enqueue "{\\"id\\":\\"jobTimeout\\",\\"command\\":\\"timeout /t 4 /nobreak\\",\\"timeout\\":2,\\"priority\\":2}"')

    ExecuteCommand("queuectl status")
    
    # TEST WORKER PROCESSING
    print("\n--- 3. STARTING WORKERS FOR 8 SECONDS ---")
    workerProcess = subprocess.Popen("queuectl worker start --count 2", shell=True)
    time.sleep(8)
    workerProcess.terminate()
    workerProcess.wait()
    print("--- WORKERS STOPPED ---")

    # VERIFYING FINAL STATES
    print("\n--- 4. VERIFYING FINAL STATES ---")
    ExecuteCommand("queuectl status")
    
    print("\n--- VERIFYING COMPLETED JOBS ---")
    ExecuteCommand("queuectl list --state completed")

    print("\n--- VERIFYING DLQ ---")
    ExecuteCommand("queuectl dlq list")

    # BONUS FEATURE TESTING
    print("\n--- 5. TESTING BONUS COMMANDS ---")
    print("\n--- TESTING LOGS ---")
    ExecuteCommand("queuectl logs jobSuccess")
    ExecuteCommand("queuectl logs jobTimeout")
    
    print("\n--- TESTING METRICS ---")
    ExecuteCommand("queuectl metrics")

    # DLQ RETRY TESTING
    print("\n--- 6. TESTING DLQ RETRY ---")
    ExecuteCommand("queuectl dlq retry jobTimeout")
    ExecuteCommand("queuectl status")

    print("\n\n--- TEST COMPLETE ---")
    print("CHECKING THE OUTPUT ABOVE TO VERIFY THAT:")
    print("1. jobHighPriority ran before jobSuccess.")
    print("2. jobScheduled was not picked up by workers (its run_at time was in the future).")
    print("3. jobTimeout failed due to timeout, retried, and ended in the DLQ.")
    print("4. Log files were created and can be viewed.")
    print("5. Metrics were calculated correctly.")

if __name__ == "__main__":
    RunTestProcess()