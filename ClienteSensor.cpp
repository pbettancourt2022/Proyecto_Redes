#include <iostream>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>

#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>

#pragma comment(lib, "ws2_32.lib") // Enlaza Winsock
#pragma comment(lib, "libssl.lib") // OpenSSL
#pragma comment(lib, "libcrypto.lib") // OpenSSL

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 9000

// Estructura de datos del sensor
struct SensorData {
    int16_t id;
    uint64_t timestamp;
    float temperatura;
    float presion;
    float humedad;
};

// Obtener timestamp actual
uint64_t get_current_timestamp() {
    return static_cast<uint64_t>(time(nullptr));
}

// Generar datos simulados
SensorData generate_sensor_data(int16_t id) {
    SensorData data;
    data.id = id;
    data.timestamp = get_current_timestamp();
    data.temperatura = 20.0f + static_cast<float>(rand()) / RAND_MAX * 10.0f;
    data.presion = 1000.0f + static_cast<float>(rand()) / RAND_MAX * 50.0f;
    data.humedad = 30.0f + static_cast<float>(rand()) / RAND_MAX * 20.0f;
    return data;
}

// Serializar datos a buffer binario
void serialize_sensor_data(const SensorData& data, unsigned char* buffer) {
    memcpy(buffer, &data.id, sizeof(data.id));
    memcpy(buffer + 2, &data.timestamp, sizeof(data.timestamp));
    memcpy(buffer + 10, &data.temperatura, sizeof(data.temperatura));
    memcpy(buffer + 14, &data.presion, sizeof(data.presion));
    memcpy(buffer + 18, &data.humedad, sizeof(data.humedad));
}

// Cifrar datos con AES-128-CBC
int encrypt_data(const unsigned char* plaintext, int plaintext_len,
                 unsigned char* key, unsigned char* iv,
                 unsigned char* ciphertext) {
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    int len;
    int ciphertext_len;

    EVP_EncryptInit_ex(ctx, EVP_aes_128_cbc(), NULL, key, iv);
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len);
    ciphertext_len = len;
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;
    EVP_CIPHER_CTX_free(ctx);

    return ciphertext_len;
}

// Calcular HMAC-SHA256
void calculate_hmac(const unsigned char* data, size_t data_len,
                    const unsigned char* key, size_t key_len,
                    unsigned char* hmac_output, unsigned int* hmac_len) {
    HMAC(EVP_sha256(), key, key_len, data, data_len, hmac_output, hmac_len);
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr)));

    // Inicializar Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "Error inicializando Winsock" << std::endl;
        return 1;
    }

    // Clave y IV
    unsigned char key[16] = {
    0x30, 0x31, 0x32, 0x33,
    0x34, 0x35, 0x36, 0x37,
    0x38, 0x39, 0x41, 0x42,
    0x43, 0x44, 0x45, 0x46};

    unsigned char hmac_key[16] = "HMAC_SECRET_KEY";

    // Crear socket
    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "Error creando socket" << std::endl;
        WSACleanup();
        return 1;
    }

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    // Conectar al servidor
    if (connect(sock, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Error conectando al servidor" << std::endl;
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    std::cout << "Conectado al servidor en " << SERVER_IP << ":" << SERVER_PORT << std::endl;

    while (true) {
        // Generar datos
        SensorData data = generate_sensor_data(42);
        unsigned char buffer[22];
        serialize_sensor_data(data, buffer);

        // Generar IV aleatorio
        unsigned char iv[16];
        RAND_bytes(iv, sizeof(iv));

        // Cifrar
        unsigned char ciphertext[64];
        int ciphertext_len = encrypt_data(buffer, sizeof(buffer), key, iv, ciphertext);

        // Calcular HMAC
        unsigned char hmac[32];
        unsigned int hmac_len;
        calculate_hmac(ciphertext, ciphertext_len, hmac_key, sizeof(hmac_key), hmac, &hmac_len);

        // Enviar IV
        send(sock, (const char*)iv, sizeof(iv), 0);

        // Enviar tamaño del paquete cifrado
        uint16_t packet_size = htons(ciphertext_len);
        send(sock, (const char*)&packet_size, sizeof(packet_size), 0);

        // Enviar ciphertext
        send(sock, (const char*)ciphertext, ciphertext_len, 0);

        // Enviar HMAC
        send(sock, (const char*)hmac, hmac_len, 0);

        // Debug UTF-8 textual
        std::string textual = "ID=" + std::to_string(data.id) +
                              " TS=" + std::to_string(data.timestamp) +
                              " T=" + std::to_string(data.temperatura) +
                              " P=" + std::to_string(data.presion) +
                              " H=" + std::to_string(data.humedad);
        std::cout << "Enviado: " << textual << " (HMAC OK)" << std::endl;

        // Esperar 5 segundos
        Sleep(5000); // Sleep en ms → 5000ms = 5s
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}
