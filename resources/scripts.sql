CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    temperature REAL,
    humidity REAL,
    distance REAL
);

CREATE TABLE IF NOT EXISTS actuator_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    actuator_name TEXT NOT NULL,
    action TEXT NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS system_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT,
    resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mqtt_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_actuator_timestamp ON actuator_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON system_alerts(timestamp);