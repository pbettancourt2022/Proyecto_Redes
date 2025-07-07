// Librerías de C++
#include <iostream>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>

// Librerías de cifrado (OpenSSL)
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>

// Enlazamos las librerías necesarias para sockets y OpenSSL
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "libssl.lib")
#pragma comment(lib, "libcrypto.lib")

// Dirección IP y puerto del servidor
#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 9000

// Estructura para representar los datos de un sensor
struct SensorData {
    int16_t id;
    uint64_t timestamp;
    float temperatura;
    float presion;
    float humedad;
};

// Obtener el tiempo actual como timestamp UNIX (segundos desde 1970)
uint64_t get_current_timestamp() {
    return static_cast<uint64_t>(time(nullptr));
}

// Genera datos aleatorios simulados para el sensor
SensorData generate_sensor_data(int16_t id) {
    SensorData data;
    data.id = id;
    data.timestamp = get_current_timestamp();
    data.temperatura = 20.0f + static_cast<float>(rand()) / RAND_MAX * 10.0f;
    data.presion = 1000.0f + static_cast<float>(rand()) / RAND_MAX * 50.0f;
    data.humedad = 30.0f + static_cast<float>(rand()) / RAND_MAX * 20.0f;
    return data;
}

// Serializa los datos del sensor a un buffer binario de 22 bytes
void serialize_sensor_data(const SensorData& data, unsigned char* buffer) {
    memcpy(buffer, &data.id, sizeof(data.id));                  // 2 bytes
    memcpy(buffer + 2, &data.timestamp, sizeof(data.timestamp)); // 8 bytes
    memcpy(buffer + 10, &data.temperatura, sizeof(data.temperatura)); // 4 bytes
    memcpy(buffer + 14, &data.presion, sizeof(data.presion));         // 4 bytes
    memcpy(buffer + 18, &data.humedad, sizeof(data.humedad));         // 4 bytes
}

// Cifra datos con AES-128-CBC
int encrypt_data(const unsigned char* plaintext, int plaintext_len,
                 unsigned char* key, unsigned char* iv,
                 unsigned char* ciphertext) {
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new(); // Crea contexto
    int len;
    int ciphertext_len;

    // Inicializa cifrado AES CBC con clave y IV
    EVP_EncryptInit_ex(ctx, EVP_aes_128_cbc(), NULL, key, iv);
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len);
    ciphertext_len = len;
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;

    EVP_CIPHER_CTX_free(ctx);
    return ciphertext_len;
}

// Calcula un HMAC SHA256 para asegurar la integridad del mensaje
void calculate_hmac(const unsigned char* data, size_t data_len,
                    const unsigned char* key, size_t key_len,
                    unsigned char* hmac_output, unsigned int* hmac_len) {
    HMAC(EVP_sha256(), key, key_len, data, data_len, hmac_output, hmac_len);
}

// Función para conectar al servidor con manejo de error
bool connect_to_server(SOCKET &sock, sockaddr_in &server_addr) {
    // Crear socket TCP
    sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "Error creando socket" << std::endl;
        return false;
    }

    // Intentar conectar
    if (connect(sock, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Error conectando al servidor" << std::endl;
        closesocket(sock);
        return false;
    }

    std::cout << "[INFO] Conectado al servidor en " << SERVER_IP << ":" << SERVER_PORT << std::endl;
    return true;
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr))); // Inicializa generador aleatorio

    // Inicializa Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "Error inicializando Winsock" << std::endl;
        return 1;
    }

    // Clave de cifrado AES de 128 bits (16 bytes)
    unsigned char key[16] = {
        0x30, 0x31, 0x32, 0x33,
        0x34, 0x35, 0x36, 0x37,
        0x38, 0x39, 0x41, 0x42,
        0x43, 0x44, 0x45, 0x46};

    // Clave para HMAC
    unsigned char hmac_key[16] = "HMAC_SECRET_KEY";

    // Configurar estructura del servidor
    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    SOCKET sock;

    // Intentamos conectar al servidor inicialmente (bloquea hasta que lo logra)
    while (!connect_to_server(sock, server_addr)) {
        std::cerr << "[REINTENTO] Reintentando conexion en 5 segundos..." << std::endl;
        Sleep(5000); // Espera 5 segundos y vuelve a intentar
    }

    while (true) {
        // Generamos los datos del sensor
        SensorData data = generate_sensor_data(42);
        unsigned char buffer[22];
        serialize_sensor_data(data, buffer);

        // IV aleatorio para el cifrado AES-CBC
        unsigned char iv[16];
        RAND_bytes(iv, sizeof(iv));

        // Cifrar los datos serializados
        unsigned char ciphertext[64];
        int ciphertext_len = encrypt_data(buffer, sizeof(buffer), key, iv, ciphertext);

        // Calcular HMAC para el mensaje cifrado
        unsigned char hmac[32];
        unsigned int hmac_len;
        calculate_hmac(ciphertext, ciphertext_len, hmac_key, sizeof(hmac_key), hmac, &hmac_len);

        // Enviar datos con manejo de errores
        bool error = false;

        // Enviar IV, tamaño del paquete, datos cifrados y HMAC
        if (send(sock, (const char*)iv, sizeof(iv), 0) <= 0) error = true;
        uint16_t packet_size = htons(ciphertext_len);
        if (send(sock, (const char*)&packet_size, sizeof(packet_size), 0) <= 0) error = true;
        if (send(sock, (const char*)ciphertext, ciphertext_len, 0) <= 0) error = true;
        if (send(sock, (const char*)hmac, hmac_len, 0) <= 0) error = true;

        if (error) {
            std::cerr << "[ERROR] Fallo en envío. Posible caída del servidor." << std::endl;
            closesocket(sock);        // Cerramos el socket actual
            WSACleanup();             // Finalizamos Winsock
            WSAStartup(MAKEWORD(2, 2), &wsaData); // Reiniciamos Winsock

            // Intentar reconectar cada 5 segundos
            while (!connect_to_server(sock, server_addr)) {
                std::cerr << "[REINTENTO] Reintentando conexión en 5 segundos..." << std::endl;
                Sleep(5000);
            }

            continue; // Ir a la siguiente iteración del loop
        }

        // Imprimir los datos enviados en texto legible
        std::string textual = "ID=" + std::to_string(data.id) +
                              " TS=" + std::to_string(data.timestamp) +
                              " T=" + std::to_string(data.temperatura) +
                              " P=" + std::to_string(data.presion) +
                              " H=" + std::to_string(data.humedad);
        std::cout << "[OK] Enviado: " << textual << " (HMAC OK)" << std::endl;

        Sleep(5000); // Espera 5 segundos antes del siguiente envío
    }

    // Nunca se alcanza, pero por buenas prácticas:
    closesocket(sock);
    WSACleanup();
    return 0;
}
