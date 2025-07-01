import socket
import struct
import hmac
import hashlib
from Crypto.Cipher import AES

# Configuración del servidor

# Dirección IP y puerto donde el servidor intermedio escuchará conexiones


SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

# Clave simétrica usada para descifrar los datos (AES-128 requiere 16 bytes)
AES_KEY = b"0123456789ABCDEF"

# Clave secreta para verificar la integridad usando HMAC-SHA256
HMAC_KEY = b"HMAC_SECRET_KEY"


# Función: Desempaquetar los datos binarios descifrados
def parsear_datos_sensor(data_bytes):
    
    # Esta función recibe los datos binarios sin cifrado y los convierte a valores legibles usando el formato:
    # ID: int16, timestamp: int64, temperatura: float, presión: float y humedad: float

    id, timestamp, temperatura, presion, humedad = struct.unpack("<H Q f f f", data_bytes)
    print("=== Datos del Sensor ===")
    print(f"ID: {id}")
    print(f"Timestamp (UNIX): {timestamp}")
    print(f"Temperatura: {temperatura:.2f} °C")
    print(f"Presión: {presion:.2f} hPa")
    print(f"Humedad: {humedad:.2f} %")
    print("========================\n")

# Aquí se inicia el servidor intermedio

# Se crea un socket TCP que usará IPv4
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
    # Asociamos el socket a la IP y el puerto definidos más arriba
    servidor.bind((SERVER_IP, SERVER_PORT))
    servidor.listen(1)
    print(f"[+] Servidor Intermedio escuchando en {SERVER_IP}:{SERVER_PORT}")

    # Esperamos que un cliente (es decir el sensor) se conecte
    conexion, direccion = servidor.accept()
    with conexion:
        print(f"[+] Conexión aceptada desde {direccion}")

        # Luego iniciamos un ciclo infinito para recibir datos continuamente
        while True:
            try:
                # Primero se recibe el IV (16 bytes)
                iv = conexion.recv(16)
                if len(iv) < 16:
                    print("[-] Error al recibir el IV (vector de inicialización)")
                    break

                # Luego se recibe el tamaño del paquete cifrado (2 bytes)
                size_bytes = conexion.recv(2)
                if len(size_bytes) < 2:
                    print("[-] Error al recibir el tamaño del paquete cifrado")
                    break
                packet_size = struct.unpack("!H", size_bytes)[0]

                # Luego se recibe el contenido cifrado 
                ciphertext = b""
                while len(ciphertext) < packet_size:
                    fragmento = conexion.recv(packet_size - len(ciphertext))
                    if not fragmento:
                        break
                    ciphertext += fragmento

                if len(ciphertext) != packet_size:
                    print("[-] Error: El paquete cifrado está incompleto")
                    break

                # Por último se recibe el HMAC 
                
                hmac_recibido = conexion.recv(32)
                if len(hmac_recibido) < 32:
                    print("[-] Error al recibir el HMAC")
                    break

                # Despues se verifica el HMAC con la clave secreta
                hmac_calculado = hmac.new(HMAC_KEY, ciphertext, hashlib.sha256).digest()

                if not hmac.compare_digest(hmac_recibido, hmac_calculado):
                    print("[-] El HMAC no coincide. Posible manipulación del paquete.")
                    continue
                else:
                    print("[+] HMAC verificado correctamente")

                # Después se desencriptan los datos
                aes = AES.new(AES_KEY, AES.MODE_CBC, iv)
                datos_descifrados = aes.decrypt(ciphertext)

                # Y por último se interpretan los datos
                parsear_datos_sensor(datos_descifrados[:22])

            except Exception as e:
                print(f"[!] Error inesperado: {e}")
                break
