"""
Cliente MQTT para Raspberry Pi Pico W con MicroPython.
Implementación integrada compatible con Wokwi (sin dependencias externas).
"""

import usocket as socket
import ustruct as struct


class SimpleMQTT:
    """Cliente MQTT minimalista para Wokwi/MicroPython."""
    
    def __init__(self, client_id, server, port=1883, user=None, password=None):
        self.client_id = client_id
        self.sock = None
        self.server = server
        self.port = port
        self.user = user
        self.pswd = password
        self.pid = 0
        self.cb = None

    def _send_str(self, s):
        """Envía una cadena con su longitud."""
        self.sock.write(struct.pack("!H", len(s)))
        self.sock.write(s)

    def _recv_len(self):
        """Recibe longitud variable MQTT."""
        n = 0
        sh = 0
        while 1:
            b = self.sock.read(1)[0]
            n |= (b & 0x7f) << sh
            if not b & 0x80:
                return n
            sh += 7

    def set_callback(self, f):
        """Establece función callback para mensajes."""
        self.cb = f

    def connect(self):
        """Conecta al broker MQTT."""
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = 0x02  # clean session
        if self.user is not None:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0

        i = 1
        while sz > 0x7f:
            premsg[i] = (sz & 0x7f) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        self.sock.write(premsg, i + 2)
        self.sock.write(msg)
        self._send_str(self.client_id)
        if self.user is not None:
            self._send_str(self.user)
            self._send_str(self.pswd)
        
        resp = self.sock.read(4)
        assert resp[0] == 0x20 and resp[1] == 0x02
        if resp[3] != 0:
            raise Exception(f"MQTT connection failed: {resp[3]}")
        return resp[2] & 1

    def disconnect(self):
        """Desconecta del broker."""
        self.sock.write(b"\xe0\0")
        self.sock.close()

    def ping(self):
        """Envía ping al broker."""
        self.sock.write(b"\xc0\0")

    def publish(self, topic, msg, retain=False, qos=0):
        """Publica mensaje en un topic."""
        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        i = 1
        while sz > 0x7f:
            pkt[i] = (sz & 0x7f) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        self.sock.write(pkt, i + 1)
        self._send_str(topic)
        if qos > 0:
            self.pid += 1
            pid = self.pid
            struct.pack_into("!H", pkt, 0, pid)
            self.sock.write(pkt, 2)
        self.sock.write(msg)

    def subscribe(self, topic, qos=0):
        """Suscribe a un topic."""
        pkt = bytearray(b"\x82\0\0\0")
        self.pid += 1
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
        self.sock.write(pkt)
        self._send_str(topic)
        self.sock.write(qos.to_bytes(1, "little"))
        while 1:
            op = self.wait_msg()
            if op == 0x90:
                resp = self.sock.read(4)
                assert resp[1] == pkt[2] and resp[2] == pkt[3]
                if resp[3] == 0x80:
                    raise Exception("Subscription failed")
                return

    def wait_msg(self):
        """Espera mensaje (bloqueante)."""
        res = self.sock.read(1)
        self.sock.setblocking(True)
        if res is None:
            return None
        if res == b"":
            raise OSError(-1)
        if res == b"\xd0":
            assert self.sock.read(1) == b"\0"
            return None
        op = res[0]
        if op & 0xf0 != 0x30:
            return op
        sz = self._recv_len()
        topic_len = self.sock.read(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = self.sock.read(topic_len)
        sz -= topic_len + 2
        if op & 6:
            pid = self.sock.read(2)
            pid = pid[0] << 8 | pid[1]
            sz -= 2
        msg = self.sock.read(sz)
        self.cb(topic, msg)
        if op & 6 == 2:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self.sock.write(pkt)
        return op

    def check_msg(self):
        """Verifica mensajes (no bloqueante)."""
        self.sock.setblocking(False)
        return self.wait_msg()


class MQTTClientWrapper:
    """
    Envoltura para cliente MQTT con Adafruit IO.
    Implementación integrada sin dependencias externas.
    """

    def __init__(self, client_id, username, aio_key, on_message_cb=None):
        self.client_id = client_id
        self.username = username
        self.aio_key = aio_key
        self.on_message_cb = on_message_cb
        self.connected = False
        
        print("📡 Inicializando cliente MQTT integrado...")
        
        # Crear cliente MQTT (usar bytes directamente)
        self.client = SimpleMQTT(
            client_id=client_id.encode() if isinstance(client_id, str) else client_id,
            server="io.adafruit.com",
            port=1883,
            user=username.encode() if isinstance(username, str) else username,
            password=aio_key.encode() if isinstance(aio_key, str) else aio_key
        )

    def connect(self):
        """Conecta al broker MQTT de Adafruit IO."""
        print("\n" + "="*60)
        print("🌐 CONECTANDO A ADAFRUIT IO MQTT")
        print("="*60)
        print(f"👤 Usuario: {self.username}")
        print(f"🔑 AIO Key: {self.aio_key[:10]}...")
        print(f"🆔 Client ID: {self.client_id}")
        print(f"🖥️  Servidor: io.adafruit.com:1883")
        print("─"*60)
        
        try:
            # Establecer callback antes de conectar
            self.client.set_callback(self._internal_callback)
            
            # Conectar al broker
            print("⏳ Estableciendo conexión...")
            self.client.connect()
            
            self.connected = True
            print("✅ CONECTADO A ADAFRUIT IO MQTT")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            print("="*60 + "\n")
            self.connected = False
            raise

    def disconnect(self):
        """Desconecta del broker MQTT."""
        if self.connected:
            print("\n🔌 Desconectando de Adafruit IO...")
            try:
                self.client.disconnect()
                self.connected = False
                print("✅ Desconectado correctamente")
            except:
                pass

    def _internal_callback(self, topic, msg):
        """
        Callback interno que procesa mensajes MQTT.
        Convierte bytes a strings y llama al callback del usuario.
        """
        if self.on_message_cb:
            try:
                # Decodificar topic y mensaje
                topic_str = topic.decode("utf-8") if isinstance(topic, bytes) else topic
                msg_str = msg.decode("utf-8") if isinstance(msg, bytes) else msg
                
                # Llamar al callback del usuario
                self.on_message_cb(topic_str, msg_str)
                
            except Exception as e:
                print(f"⚠️ Error en callback: {e}")

    def subscribe_feed(self, feed_name):
        """
        Suscribe a un feed de Adafruit IO.
        
        Args:
            feed_name (str): Nombre del feed (sin el prefijo username/feeds/)
        """
        if not self.connected:
            print("⚠️  No conectado a MQTT")
            return
        
        # Construir topic completo
        topic = f"{self.username}/feeds/{feed_name}"
        
        try:
            # Suscribirse al topic (convertir a bytes)
            topic_bytes = topic.encode() if isinstance(topic, str) else topic
            self.client.subscribe(topic_bytes)
            print(f"📥 SUSCRITO a feed: {feed_name}")
            print(f"   Topic: {topic}")
            
        except Exception as e:
            print(f"❌ Error al suscribirse a {feed_name}: {e}")

    def publish_feed(self, feed_name, payload):
        """
        Publica un valor en un feed de Adafruit IO.
        
        Args:
            feed_name (str): Nombre del feed
            payload: Valor a publicar (se convierte a string)
        """
        if not self.connected:
            print("⚠️  No conectado a MQTT")
            return
        
        # Construir topic completo
        topic = f"{self.username}/feeds/{feed_name}"
        
        try:
            # Convertir payload y topic a bytes
            payload_str = str(payload)
            topic_bytes = topic.encode() if isinstance(topic, str) else topic
            payload_bytes = payload_str.encode() if isinstance(payload_str, str) else payload_str
            
            # Publicar
            self.client.publish(topic_bytes, payload_bytes)
            print(f"📤 PUBLICADO → {feed_name}: {payload}")
            
        except Exception as e:
            print(f"❌ Error al publicar en {feed_name}: {e}")

    def check_messages(self):
        """
        Verifica si hay mensajes MQTT pendientes.
        Modo no bloqueante - retorna inmediatamente.
        """
        if not self.connected:
            return
        
        try:
            # check_msg() es no bloqueante
            self.client.check_msg()
            
        except OSError as e:
            # OSError es común en modo no bloqueante (sin mensajes)
            pass
            
        except Exception as e:
            print(f"⚠️ Error en check_messages: {e}")

    def ping(self):
        """Envía un ping al broker para mantener la conexión activa."""
        if self.connected:
            try:
                self.client.ping()
            except:
                pass