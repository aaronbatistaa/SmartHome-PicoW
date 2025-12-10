import time
from config_loader import load_config
from wifi_manager import connect_wifi
from sensors import DHT22Sensor, HCSR04Sensor
from actuators import Led, Buzzer
from mqtt_client import MQTTClientWrapper
from database import IoTDatabase

# Pines usados (según diagram.json)
PIN_DHT = 15
PIN_TRIG = 5
PIN_ECHO = 4
PIN_LED = 2
PIN_BUZZER = 3

# Estado global de actuadores controlados por la nube
led = None
buzzer = None
db = None
mqtt = None

def on_mqtt_message(topic, msg):
    """
    Callback para mensajes MQTT desde Adafruit IO.
    Recibe comandos desde la nube y controla actuadores.
    """
    global led, buzzer, db
    
    print("\n" + "="*60)
    print("MENSAJE MQTT RECIBIDO DESDE LA NUBE")
    print("="*60)
    print("Topic:", topic)
    print("Mensaje:", msg)
    print("-"*60)

    # Identificar feed a partir del topic
    if topic.endswith("/led-cmd"):
        if msg.upper() == "ON":
            led.on()
            db.log_actuator_event("LED", "ON", "mqtt")
            print("=> LED ENCENDIDO")
            print("=> Evento guardado en BD")
        else:
            led.off()
            db.log_actuator_event("LED", "OFF", "mqtt")
            print("=> LED APAGADO")
            print("=> Evento guardado en BD")

    elif topic.endswith("/buzzer-cmd"):
        if msg.upper() == "ON":
            buzzer.on()
            db.log_actuator_event("Buzzer", "ON", "mqtt")
            print("=> BUZZER ENCENDIDO")
            print("=> Evento guardado en BD")
        else:
            buzzer.off()
            db.log_actuator_event("Buzzer", "OFF", "mqtt")
            print("=> BUZZER APAGADO")
            print("=> Evento guardado en BD")
    
    print("="*60 + "\n")


def check_alerts(temp, hum, dist):
    """
    Verifica condiciones y genera alertas si es necesario.
    
    Args:
        temp: Temperatura actual
        hum: Humedad actual
        dist: Distancia actual
        
    Returns:
        bool: True si se generó alguna alerta
    """
    global db, led, buzzer
    
    alerts_triggered = False
    
    # Alerta: Temperatura alta
    if temp and temp > 30:
        db.create_alert(
            "temperature_high",
            f"Temperatura elevada: {temp}°C",
            "warning"
        )
        print("ALERTA: Temperatura alta detectada")
        alerts_triggered = True
    
    # Alerta: Humedad baja
    if hum and hum < 30:
        db.create_alert(
            "humidity_low",
            f"Humedad baja: {hum}%",
            "warning"
        )
        print("ALERTA: Humedad baja detectada")
        alerts_triggered = True
    
    # Alerta: Objeto cercano detectado
    if dist and dist < 10:
        db.create_alert(
            "distance_close",
            f"Objeto detectado a {dist}cm",
            "info"
        )
        print("ALERTA: Objeto cercano detectado")
        print("Activando buzzer automaticamente...")
        
        # Activar buzzer automáticamente
        buzzer.on()
        db.log_actuator_event("Buzzer", "ON", "auto")
        time.sleep(0.5)
        buzzer.off()
        db.log_actuator_event("Buzzer", "OFF", "auto")
        alerts_triggered = True
    
    return alerts_triggered


def main():
    global led, buzzer, db, mqtt

    print("\n" + "="*60)
    print("SISTEMA IoT SMART HOME - PICO W")
    print("="*60 + "\n")

    # 1) Inicializar base de datos
    print("PASO 1/7 - Inicializando base de datos...")
    db = IoTDatabase("iot_smart_home.db")
    db.log_mqtt_event("system_start", "Sistema iniciado")
    print("=> Base de datos lista\n")

    # 2) Cargar configuración
    print("PASO 2/7 - Cargando configuracion...")
    config = load_config()
    ssid = config["wifi_ssid"]
    pwd = config["wifi_password"]
    username = config["adafruit_username"]
    aio_key = config["adafruit_key"]
    client_id = config["mqtt_client_id"]
    feeds = config["feeds"]
    print("=> Configuracion cargada")
    print("   WiFi:", ssid)
    print("   Usuario Adafruit:", username)
    print()

    # 3) Conectar a WiFi
    print("PASO 3/7 - Conectando a WiFi...")
    try:
        wlan = connect_wifi(ssid, pwd)
        db.log_mqtt_event("wifi_connect", f"Conectado a {ssid}")
        print("=> WiFi conectado exitosamente\n")
    except Exception as e:
        print("ERROR WiFi:", e)
        db.log_mqtt_event("wifi_error", str(e))
        return

    # 4) Inicializar sensores y actuadores
    print("PASO 4/7 - Inicializando hardware...")
    try:
        dht = DHT22Sensor(PIN_DHT)
        dist = HCSR04Sensor(PIN_TRIG, PIN_ECHO)
        led = Led(PIN_LED)
        buzzer = Buzzer(PIN_BUZZER)
        print("=> Hardware inicializado")
        print("   - DHT22 (Temp/Hum) en GP15")
        print("   - HC-SR04 (Dist) en GP5/GP4")
        print("   - LED en GP2")
        print("   - Buzzer en GP3")
        print()
    except Exception as e:
        print("ERROR inicializando hardware:", e)
        return

    # 5) Configurar cliente MQTT
    print("PASO 5/7 - Configurando MQTT...")
    mqtt = MQTTClientWrapper(
        client_id=client_id,
        username=username,
        aio_key=aio_key,
        on_message_cb=on_mqtt_message
    )
    
    try:
        mqtt.connect()
        db.log_mqtt_event("mqtt_connect", "Conectado a Adafruit IO")
        print("=> MQTT conectado exitosamente\n")
    except Exception as e:
        print("ERROR MQTT:", e)
        print("Detalles:", str(e))
        db.log_mqtt_event("mqtt_error", str(e))
        print("\nContinuando sin MQTT...\n")
        mqtt = None

    # 6) Suscribirse a feeds de comando
    if mqtt and mqtt.connected:
        print("PASO 6/7 - Suscribiendose a feeds de control...")
        try:
            mqtt.subscribe_feed(feeds["led_cmd"])
            mqtt.subscribe_feed(feeds["buzzer_cmd"])
            db.log_mqtt_event("mqtt_subscribe", f"Feeds: {feeds['led_cmd']}, {feeds['buzzer_cmd']}")
            print("=> Suscripciones completadas\n")
        except Exception as e:
            print("ERROR en suscripciones:", e)

    # 7) Información del sistema
    print("PASO 7/7 - Informacion del sistema:")
    print("   - Lecturas cada 5 segundos")
    print("   - Publicacion automatica a Adafruit IO")
    print("   - Escucha de comandos desde la nube")
    print("   - Almacenamiento en base de datos local")
    print("   - Alertas automaticas activadas")
    print("\nCONTROL REMOTO DISPONIBLE:")
    print("   - Envia 'ON' o 'OFF' al feed 'led-cmd'")
    print("   - Envia 'ON' o 'OFF' al feed 'buzzer-cmd'")
    print()

    # 8) Bucle principal
    print("="*60)
    print("SISTEMA EN FUNCIONAMIENTO")
    print("="*60 + "\n")
    
    last_pub = 0
    last_ping = 0
    INTERVALO_PUB = 5  # segundos
    INTERVALO_PING = 60  # segundos (mantener conexión MQTT)
    reading_count = 0

    try:
        while True:
            now = time.time()
            
            # Procesar mensajes MQTT entrantes
            if mqtt and mqtt.connected:
                try:
                    mqtt.check_messages()
                except Exception as e:
                    print("Error en check_messages:", e)
            
            # Enviar ping MQTT periódicamente
            if mqtt and mqtt.connected and (now - last_ping >= INTERVALO_PING):
                last_ping = now
                try:
                    mqtt.ping()
                except:
                    pass

            # Leer sensores y publicar
            if now - last_pub >= INTERVALO_PUB:
                last_pub = now
                reading_count += 1

                # Leer sensores
                try:
                    dht_values = dht.read()
                    temp = dht_values["temperature"]
                    hum = dht_values["humidity"]
                except Exception as e:
                    print("Error leyendo DHT22:", e)
                    temp = None
                    hum = None

                try:
                    dist_cm = dist.read_cm()
                except Exception as e:
                    print("Error leyendo HC-SR04:", e)
                    dist_cm = None

                # Mostrar lecturas
                print("\n--- LECTURA #" + str(reading_count) + " ---")
                print("Temperatura:", temp, "C")
                print("Humedad:", hum, "%")
                print("Distancia:", dist_cm, "cm")

                # Guardar en base de datos
                try:
                    record_id = db.insert_sensor_reading(temp, hum, dist_cm)
                    if record_id:
                        print("Guardado en BD (ID:", str(record_id) + ")")
                except Exception as e:
                    print("Error guardando en BD:", e)

                # Verificar alertas
                try:
                    if check_alerts(temp, hum, dist_cm):
                        print("Alertas generadas")
                except Exception as e:
                    print("Error en alertas:", e)

                # Publicar en Adafruit IO
                if mqtt and mqtt.connected:
                    try:
                        mqtt.publish_feed(feeds["temperature"], temp)
                        mqtt.publish_feed(feeds["humidity"], hum)
                        if dist_cm is not None:
                            mqtt.publish_feed(feeds["distance"], dist_cm)
                        db.log_mqtt_event("mqtt_publish", f"Temp:{temp}, Hum:{hum}, Dist:{dist_cm}")
                        print("Publicado en Adafruit IO")
                    except Exception as e:
                        print("Error publicando:", e)
                else:
                    print("MQTT no conectado (datos no enviados)")
                
                print("-"*40)
                
                # Mostrar estadísticas cada 10 lecturas
                if reading_count % 10 == 0:
                    print("\n" + "="*60)
                    print("ESTADISTICAS DEL SISTEMA")
                    print("="*60)
                    
                    try:
                        stats = db.get_database_stats()
                        print("Lecturas guardadas:", stats.get('sensor_readings_count', 0))
                        print("Eventos de actuadores:", stats.get('actuator_events_count', 0))
                        print("Alertas generadas:", stats.get('system_alerts_count', 0))
                        print("Logs MQTT:", stats.get('mqtt_logs_count', 0))
                        
                        averages = db.get_average_readings(1)
                        print("\nPROMEDIOS:")
                        print("  Temp:", averages.get('avg_temperature', 'N/A'), "C")
                        print("  Hum:", averages.get('avg_humidity', 'N/A'), "%")
                        print("  Dist:", averages.get('avg_distance', 'N/A'), "cm")
                        print("="*60 + "\n")
                    except Exception as e:
                        print("Error obteniendo estadisticas:", e)
                        print("="*60 + "\n")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("DETENIENDO SISTEMA")
        print("="*60)
    
    finally:
        # Limpieza
        print("\nLimpiando recursos...")
        
        if mqtt:
            try:
                mqtt.disconnect()
            except:
                pass
        
        try:
            db.log_mqtt_event("system_stop", "Sistema detenido")
        except:
            pass
        
        # Mostrar resumen final
        print("\n" + "="*60)
        print("RESUMEN FINAL DEL SISTEMA")
        print("="*60)
        
        try:
            stats = db.get_database_stats()
            for key, value in stats.items():
                print(key + ":", value)
        except Exception as e:
            print("Error obteniendo resumen:", e)
        
        print("="*60)
        
        try:
            db.close()
        except:
            pass
        
        print("\nSistema cerrado correctamente\n")


# Ejecutar main
if __name__ == "__main__":
    main()