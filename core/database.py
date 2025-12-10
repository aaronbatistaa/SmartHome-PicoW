import time

class IoTDatabase:
    """
    Base de datos en memoria para Wokwi (sin SQLite).
    Compatible con el main.py actual.
    """

    def __init__(self, db_path="iot_data"):
        print("📁 Base en memoria inicializada:", db_path)
        self.sensor_readings = []
        self.actuator_events = []
        self.system_alerts = []
        self.mqtt_logs = []
        self._id_counter = 1

    def _ts(self):
        return time.time()

    # --- SENSOR DATA ---
    def insert_sensor_reading(self, temperature=None, humidity=None, distance=None):
        record = {
            "id": self._id_counter,
            "timestamp": self._ts(),
            "temperature": temperature,
            "humidity": humidity,
            "distance": distance,
        }
        self.sensor_readings.append(record)
        self._id_counter += 1
        return record["id"]

    # --- ACTUATOR EVENTS ---
    def log_actuator_event(self, name, action, source="local"):
        record = {
            "id": self._id_counter,
            "timestamp": self._ts(),
            "actuator": name,
            "action": action,
            "source": source
        }
        self.actuator_events.append(record)
        self._id_counter += 1
        return record["id"]

    # --- ALERTS ---
    def create_alert(self, alert_type, message, severity="info"):
        record = {
            "id": self._id_counter,
            "timestamp": self._ts(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "resolved": False
        }
        self.system_alerts.append(record)
        self._id_counter += 1
        return record["id"]

    # --- MQTT LOGS ---
    def log_mqtt_event(self, event_type, details=""):
        record = {
            "id": self._id_counter,
            "timestamp": self._ts(),
            "event_type": event_type,
            "details": details
        }
        self.mqtt_logs.append(record)
        self._id_counter += 1
        return record["id"]

    # --- STATS ---
    def get_database_stats(self):
        return {
            "sensor_readings_count": len(self.sensor_readings),
            "actuator_events_count": len(self.actuator_events),
            "system_alerts_count": len(self.system_alerts),
            "mqtt_logs_count": len(self.mqtt_logs),
        }

    def close(self):
        print("🔒 Base en memoria cerrada.")
