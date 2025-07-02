import requests
import time

# Configuración
API_URL = " " #Aquí debe ir el IP del servidor final  
INTERVALO_SEGUNDOS = 5  # Cada cuánto tiempo consulta la API

# Definicion de rangos normales de temperatura, presión y humedad
TEMP_MIN, TEMP_MAX = 0.0, 100.0
PRES_MIN, PRES_MAX = 800.0, 2000.0
HUM_MIN, HUM_MAX = 10.0, 90.0


def analizar_dato(dato):  #funcion para analizar un dato
    id_sensor = dato.get("id", "desconocido")
    temp = dato.get("temperatura")
    pres = dato.get("presion")
    hum = dato.get("humedad")
    
    if temp is not None and (temp < TEMP_MIN or temp > TEMP_MAX):#Verifica si la temperatura está fuera de rango
        print(f"ALERTA: Sensor {id_sensor} temperatura fuera de rango: {temp}°C")
    if pres is not None and (pres < PRES_MIN or pres > PRES_MAX):#Verifica si la presión está fuera de rango
        print(f"ALERTA: Sensor {id_sensor} presión fuera de rango: {pres} hPa")
    if hum is not None and (hum < HUM_MIN or hum > HUM_MAX):#Verifica si la humedad está fuera de rango 
        print(f"ALERTA: Sensor {id_sensor} humedad fuera de rango: {hum}%")

def consultar_api():  #función que consulta la API REST
    try:
        response = requests.get(API_URL)  #Intenta hacer una petición GET a la URL
        if response.status_code == 200:
            datos = response.json()
            for dato in datos:
                analizar_dato(dato)
        else:
            print("Error al consultar API:", response.status_code)
    except Exception as e:
        print("Excepción al consultar API:", str(e))

# Bucle principal
print("Iniciando cliente de consulta...")
while True:
    consultar_api()  #Consulta la API y revisa si hay datos anómalos
    time.sleep(INTERVALO_SEGUNDOS)  #Espera el tiempo configurado antes de volver a consultar
