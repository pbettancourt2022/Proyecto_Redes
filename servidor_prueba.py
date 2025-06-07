import socket
import struct
import hmac
import hashlib
from Crypto.Cipher import AES

# Configuración
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

# Clave y claves HMAC (deben coincidir con las del cliente)
AES_KEY = b"0123456789ABCDEF"
HMAC_KEY = b"HMAC_SECRET_KEY!"  # misma clave que cliente (asegúrate de que sea de 16 bytes)

# Función para desempaquetar los datos binarios
def parse_sensor_data(data):
    id, timestamp, temperatura, presion, humedad = struct.unpack("<H Q f f f", data)
    print(f"ID={id}, Timestamp={timestamp}, Temp={temperatura:.2f}°C, "
          f"Presion={presion:.2f} hPa, Humedad={humedad:.2f}%")

# Crear socket TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    print(f"[+] Servidor escuchando en {SERVER_IP}:{SERVER_PORT} ...")

    conn, addr = server_socket.accept()
    with conn:
        print(f"[+] Conexión aceptada desde {addr}")

        while True:
            try:
                # Recibir IV
                iv = conn.recv(16)
                if len(iv) < 16:
                    print("[-] Error al recibir IV")
                    break

                # Recibir tamaño del paquete cifrado
                packet_size_bytes = conn.recv(2)
                if len(packet_size_bytes) < 2:
                    print("[-] Error al recibir tamaño del paquete")
                    break

                packet_size = struct.unpack("!H", packet_size_bytes)[0]

                # Recibir paquete cifrado
                ciphertext = b""
                while len(ciphertext) < packet_size:
                    chunk = conn.recv(packet_size - len(ciphertext))
                    if not chunk:
                        break
                    ciphertext += chunk

                if len(ciphertext) != packet_size:
                    print("[-] Error al recibir ciphertext completo")
                    break

                # Recibir HMAC
                hmac_received = conn.recv(32)
                if len(hmac_received) < 32:
                    print("[-] Error al recibir HMAC")
                    break

                # Verificar HMAC
                hmac_calculated = hmac.new(HMAC_KEY, ciphertext, hashlib.sha256).digest()

                if hmac.compare_digest(hmac_received, hmac_calculated):
                    print("[+] HMAC OK")
                else:
                    print("[-] HMAC inválido")
                    continue

                # Desencriptar
                cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
                decrypted_data = cipher.decrypt(ciphertext)

                # Los datos de sensor ocupan 22 bytes
                parse_sensor_data(decrypted_data[:22])

                print("-" * 50)

            except Exception as e:
                print(f"[-] Error: {e}")
                break
