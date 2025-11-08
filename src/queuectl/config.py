# config.py - MANAGES ALL CONFIGURATION SETTINGS (UPDATED TO PREVENT FILE LOCKS)
from .db import GetDbConnection, Query

DefaultConfig = {
    'maxRetries': 3,
    'backoffBase': 2,
}

def GetConfigValue(configKey):
    """Gets a config value, opening and closing the DB connection."""
    db = GetDbConnection()
    ConfigTable = db.table('Config')
    ConfigQuery = Query()
    result = ConfigTable.get(ConfigQuery.key == configKey)
    db.close()
    return result['value'] if result else DefaultConfig.get(configKey)

def SetConfigValue(configKey, configValue):
    """Sets a config value, opening and closing the DB connection."""
    db = GetDbConnection()
    ConfigTable = db.table('Config')
    ConfigQuery = Query()
    ConfigTable.upsert({'key': configKey, 'value': configValue}, ConfigQuery.key == configKey)
    db.close()