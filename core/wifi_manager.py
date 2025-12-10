"""
Gestor de conexión WiFi para Raspberry Pi Pico W.
Compatible con MicroPython 1.24+
"""

import network
import time

def connect_wifi(ssid, password, max_wait=20):
    """Conecta la Raspberry Pi Pico W a una red WiFi."""
    print("\n" + "="*60)
    print("📡 CONECTANDO A WIFI")
    print("="*60)
    print(f"🌐 SSID: {ssid}")
    print("─"*60)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        print("✅ Ya conectado a WiFi")
        ip = wlan.ifconfig()[0]
        print(f"📍 IP: {ip}")
        print("="*60 + "\n")
        return wlan
    
    print("⏳ Conectando a la red...")
    wlan.connect(ssid, password)
    
    wait = 0
    while not wlan.isconnected() and wait < max_wait:
        print(f"   Intentando... {wait}s / {max_wait}s")
        time.sleep(1)
        wait += 1
    
    if not wlan.isconnected():
        wlan.active(False)
        print("❌ No se pudo conectar a la red WiFi")
        print("="*60 + "\n")
        raise RuntimeError(f"No se pudo conectar a '{ssid}' después de {max_wait}s")
    
    ip, subnet, gateway, dns = wlan.ifconfig()
    
    print("✅ CONECTADO A WIFI")
    print("─"*60)
    print(f"📍 IP: {ip}")
    print(f"🌐 Subnet: {subnet}")
    print(f"🚪 Gateway: {gateway}")
    print(f"🔍 DNS: {dns}")
    print(f"📶 RSSI: {wlan.status('rssi')} dBm")
    print("="*60 + "\n")
    
    return wlan


def disconnect_wifi():
    """Desconecta de la red WiFi."""
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            print("📡 Desconectando WiFi...")
            wlan.disconnect()
            wlan.active(False)
            print("✅ WiFi desconectado")
    except Exception as e:
        print(f"⚠️ Error al desconectar WiFi: {e}")


def get_wifi_status():
    """Obtiene el estado actual de la conexión WiFi."""
    wlan = network.WLAN(network.STA_IF)
    
    if not wlan.active():
        return {
            "status": "inactive",
            "connected": False,
            "message": "WiFi no está activo"
        }
    
    if not wlan.isconnected():
        return {
            "status": "disconnected",
            "connected": False,
            "message": "WiFi activo pero no conectado"
        }
    
    ip, subnet, gateway, dns = wlan.ifconfig()
    
    return {
        "status": "connected",
        "connected": True,
        "ip": ip,
        "subnet": subnet,
        "gateway": gateway,
        "dns": dns,
        "rssi": wlan.status('rssi')
    }