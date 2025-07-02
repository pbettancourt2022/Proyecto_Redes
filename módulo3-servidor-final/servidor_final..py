from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = 'sensores.db'

# Crear base de datos si no existe
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS datos (
            id INTEGER,
            fecha_hora TEXT,
            temperatura REAL,
            presion REAL,
            humedad REAL
        )
    ''')
    conn.commit()
    conn.close()

# Ruta POST: recibe datos del sensor desde el servidor intermedio 
@app.route('/datos', methods=['POST'])
def recibir_datos():
    data = request.get_json()

    print("\n========================================================================\n")

    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400

    print("Datos recibidos:", data)

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO datos (id, fecha_hora, temperatura, presion, humedad)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['id'],
            data['fecha_hora'],
            data['temperatura'],
            data['presion'],
            data['humedad']
        ))
        conn.commit()
        conn.close()
        print("\033[1;32mDatos guardados en la base de datos\033[0m\n")  # <-- Confirmación
        return jsonify({"mensaje": "Datos guardados exitosamente"}), 201
    except Exception as e:
        print(f"\033[1;31mError al guardar datos: {e}\033[0m")
        return jsonify({"error": str(e)}), 400


# Ruta GET: consulta los últimos 3 datos
@app.route('/datos', methods=['GET'])
def obtener_datos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM datos ORDER BY fecha_hora DESC LIMIT 3')
    filas = c.fetchall()
    conn.close()

    resultado = [
        {"id": f[0], "fecha_hora": f[1], "temperatura": f[2],
         "presion": f[3], "humedad": f[4]}
        for f in filas
    ]
    return jsonify(resultado)

# Inicializa y corre el servidor
if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)
