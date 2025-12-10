from machine import Pin, time_pulse_us
import dht
import utime
import random

class DHT22Sensor:
    """Maneja sensor DHT22 (temperatura y humedad)."""

    def __init__(self, pin_num):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._sensor = dht.DHT22(self._pin)
        # Valores base para simulación realista
        self._base_temp = 24.0
        self._base_hum = 40.0

    def read(self):
        """Retorna un dict con temperatura (°C) y humedad (%)."""
        self._sensor.measure()
        temp_raw = self._sensor.temperature()
        hum_raw = self._sensor.humidity()
        
        # Agregar variación realista para simulación
        # En hardware real esto no sería necesario
        temp_variation = (random.random() - 0.5) * 2.0  # ±1°C
        hum_variation = (random.random() - 0.5) * 5.0   # ±2.5%
        
        temp = round(temp_raw + temp_variation, 1)
        hum = round(hum_raw + hum_variation, 1)
        
        # Limitar rangos realistas
        temp = max(15.0, min(35.0, temp))  # 15-35°C
        hum = max(20.0, min(80.0, hum))    # 20-80%
        
        return {
            "temperature": temp,
            "humidity": hum
        }


class HCSR04Sensor:
    """Maneja sensor de distancia HC-SR04."""

    def __init__(self, trig_pin, echo_pin):
        self._trig = Pin(trig_pin, Pin.OUT)
        self._echo = Pin(echo_pin, Pin.IN)
        self._base_distance = 50.0

    def read_cm(self, timeout_us=30000):
        """Mide la distancia en centímetros."""
        # pulso de disparo
        self._trig.value(0)
        utime.sleep_us(2)
        self._trig.value(1)
        utime.sleep_us(10)
        self._trig.value(0)

        # medir pulso de eco (alto)
        try:
            duration = time_pulse_us(self._echo, 1, timeout_us)
        except OSError:
            # timeout
            return None

        # conversión a cm (velocidad del sonido ~340 m/s)
        distance_cm = (duration / 2) / 29.1
        
        # Agregar variación realista para simulación
        # Simula pequeños movimientos del objeto
        variation = (random.random() - 0.5) * 10.0  # ±5cm
        distance_cm = distance_cm + variation
        
        # Limitar a rango válido del sensor (2-400cm)
        distance_cm = max(2.0, min(400.0, distance_cm))
        
        return round(distance_cm, 2)