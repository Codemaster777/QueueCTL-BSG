# db.py - HANDLES DATABASE INITIALIZATION AND ACCESS
import threading
from tinydb import TinyDB, Query

# A GLOBAL LOCK TO PREVENT PHYSICAL RACE CONDITIONS ON THE DATABASE FILE
DatabaseLock = threading.Lock()

# A QUERY OBJECT FOR SEARCHING
JobQuery = Query()

def GetDbConnection():
    """Creates a new TinyDB instance for an operation."""
    return TinyDB('jobs_database.json')