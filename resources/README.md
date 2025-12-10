# Smart Home IoT System – Raspberry Pi Pico W

Sistema IoT modular basado en **Raspberry Pi Pico W**, con monitoreo de sensores, control de actuadores, comunicación MQTT con **Adafruit IO**, registro de datos y backend externo con **SQLite**.  
Diseñado para funcionar tanto en **Wokwi** como en hardware real.

---

## 📌 Características Principales

- Lectura periódica de sensores:
  - DHT22 → Temperatura / Humedad  
  - HC-SR04 → Distancia por ultrasonido  
- Control remoto de actuadores:
  - LED  
  - Buzzer  
- Integración con **Adafruit IO (MQTT)**:
  - Publicación automática de lecturas  
  - Recepción de comandos (“ON”, “OFF”)  
- Alertas inteligentes:
  - Temperatura alta  
  - Humedad baja  
  - Objeto cercano (activa buzzer automáticamente)  
- Base de datos en memoria para Wokwi  
- Backend externo opcional con **SQLite + MQTT** para almacenamiento persistente  

---

## 📁 Estructura del Proyecto

SmartHome-PicoW/
│
├── main.py
├── diagram.json
├── config_device.json
├── requirements.txt
│
├── core/
│ ├── sensors.py
│ ├── actuators.py
│ ├── wifi_manager.py
│ ├── mqtt_client.py
│ ├── database.py
│ └── config_loader.py
│
├── backend/
│ └── backend.py
│
└── resources/
├── arquitectura.png
├── circuito_wokwi.png
└── README.md


---

# 🧱 Descripción de Módulos

| Archivo | Función |
|--------|---------|
| **main.py** | Ciclo principal, lectura de sensores, publicación MQTT, alertas |
| **sensors.py** | Manejo del DHT22 y HC-SR04 |
| **actuators.py** | Control del LED y Buzzer |
| **wifi_manager.py** | Conexión WiFi Pico W |
| **mqtt_client.py** | Cliente MQTT implementado manualmente (MicroPython) |
| **database.py** | Base de datos en memoria para Wokwi |
| **config_loader.py** | Carga de configuración JSON |
| **backend/backend.py** | Servicio externo con SQLite y paho-mqtt |
| **config_device.json** | Configuración real (no se sube al repo) |
| **config_device.example.json** | Plantilla sin credenciales |

---

# ☁️ Arquitectura del Sistema IoT

  ┌──────────────────────────┐
  │      Sensores            │
  │  DHT22 / HC-SR04         │
  └────────────┬─────────────┘
               │
               ▼
    ┌────────────────────┐
    │ Raspberry Pi Pico W│
    │  - Lecturas        │
    │  - Control LED     │
    │  - Control Buzzer  │
    │  - Alertas         │
    └───────┬────────────┘
            │ WiFi + MQTT
            ▼
   ┌────────────────────────┐
   │     Adafruit IO        │
   │  Feeds / Dashboards    │
   └─────────┬──────────────┘
             │ MQTT
             ▼
   ┌────────────────────────┐
   │ Backend Externo (PC)   │
   │  - SQLite              │
   │  - Registro completo   │
   └────────────────────────┘

## Requerimientos

paho-mqtt==1.6.1



## Configuración (config_device.json)

{
  "wifi_ssid": "TU_SSID",
  "wifi_password": "TU_PASSWORD",
  "adafruit_username": "TU_USUARIO_ADAFRUIT",
  "adafruit_key": "TU_AIO_KEY",
  "mqtt_client_id": "pico-w-smart-home",
  "feeds": {
    "temperature": "temperatura",
    "humidity": "humedad",
    "distance": "distancia",
    "led_cmd": "led-cmd",
    "buzzer_cmd": "buzzer-cmd"
  }
}

## Ejecución del Proyecto

Abrir https://wokwi.com

Importar todos los archivos

Correr main.py
