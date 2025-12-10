import json
import sqlite3
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
with open("config_device.json") as f:
    cfg = json.load(f)

AIO_USER = cfg["adafruit_username"]
AIO_KEY = cfg["adafruit_key"]

DB_PATH = "iot_data.db"

FEEDS = cfg["feeds"]


# -------------------------------
# BASE DE DATOS SQLITE
# -------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def insert_sensor(sensor, value):
    cur.execute("""
        INSERT INTO sensor_readings (timestamp, temperature, humidity, distance)
        VALUES (?, ?, ?, ?)
    """, (
        time.time(),
        value if sensor == FEEDS["temperature"] else None,
        value if sensor == FEEDS["humidity"] else None,
        value if sensor == FEEDS["distance"] else None,
    ))
    conn.commit()

def insert_actuator(actuator, action):
    cur.execute("""
        INSERT INTO actuator_events (timestamp, actuator_name, action)
        VALUES (?, ?, ?)
    """, (time.time(), actuator, action))
    conn.commit()

def insert_log(event_type, detail):
    cur.execute("""
        INSERT INTO mqtt_logs (timestamp, event_type, details)
        VALUES (?, ?, ?)
    """, (time.time(), event_type, detail))
    conn.commit()


# -------------------------------
# MQTT CALLBACKS
# -------------------------------
def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(f"{AIO_USER}/feeds/#")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    print("MSG:", topic, payload)

    insert_log("recv", f"{topic}:{payload}")

    feed = topic.split("/")[-1]

    if feed in (FEEDS["temperature"], FEEDS["humidity"], FEEDS["distance"]):
        insert_sensor(feed, float(payload))

    elif feed in (FEEDS["led_cmd"], FEEDS["buzzer_cmd"]):
        insert_actuator(feed, payload)


# -------------------------------
# MQTT CLIENT
# -------------------------------
client = mqtt.Client()
client.username_pw_set(AIO_USER, AIO_KEY)
client.on_connect = on_connect
client.on_message = on_message

client.connect("io.adafruit.com", 1883, 60)

print("Backend IoT iniciado. Escuchando mensajes MQTT...")

client.loop_forever()
