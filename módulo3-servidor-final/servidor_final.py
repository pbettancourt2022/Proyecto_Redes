from flask import Flask, request, jsonify, render_template_string
import sqlite3
import statistics

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

# Ruta GET: consulta el último dato registrado
@app.route('/datos', methods=['GET'])
def obtener_dato_mas_reciente():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM datos ORDER BY fecha_hora DESC LIMIT 1')
    fila = c.fetchone()
    resultado = []
    if fila:
        resultado.append({
            "id": fila[0],
            "fecha_hora": fila[1],
            "temperatura": fila[2],
            "presion": fila[3],
            "humedad": fila[4]
        })
        return jsonify(resultado)
    else:
        return jsonify({"error": "No hay datos disponibles"}), 404

# Ruta que renderiza el dashboard web con la visualización de datos de sensores.
# Se accede a través de /dashboard en el navegador.
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM datos ORDER BY fecha_hora DESC LIMIT 20')
    filas = c.fetchall()
    conn.close()

    # Extraer listas por variable
    temperaturas = [f[2] for f in filas]
    presiones = [f[3] for f in filas]
    humedades = [f[4] for f in filas]

    def resumen(lista):
        if not lista:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(lista),
            "max": max(lista),
            "avg": round(statistics.mean(lista), 2)
        }

    resumen_temp = resumen(temperaturas)
    resumen_pres = resumen(presiones)
    resumen_hum = resumen(humedades)

    html = '''
        <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Sensores</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #f7f9fc;
                color: #333;
                padding: 30px;
            }
            h2 {
                text-align: center;
                color: #1f3b4d;
            }
            .estadisticas {
                margin-top: 30px;
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
            }
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 20px;
                margin: 10px;
                width: 280px;
            }
            .card h3 {
                margin-top: 0;
                color: #4a90e2;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 30px;
                background-color: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            th, td {
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
                text-align: center;
            }
            th {
                background-color: #4a90e2;
                color: white;
                font-weight: normal;
            }
            tr:hover {
                background-color: #f1f7ff;
            }
            .alerta {
                background-color: #ffe6e6 !important;
                color: #b30000;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h2>Monitoreo de Sensores</h2>

        <div class="estadisticas">
            <div class="card">
                <h3>Temperatura (°C)</h3>
                <p>Promedio: {{ resumen_temp.avg }}</p>
                <p>Mínimo: {{ resumen_temp.min }}</p>
                <p>Máximo: {{ resumen_temp.max }}</p>
            </div>
            <div class="card">
                <h3>Presión (hPa)</h3>
                <p>Promedio: {{ resumen_pres.avg }}</p>
                <p>Mínimo: {{ resumen_pres.min }}</p>
                <p>Máximo: {{ resumen_pres.max }}</p>
            </div>
            <div class="card">
                <h3>Humedad (%)</h3>
                <p>Promedio: {{ resumen_hum.avg }}</p>
                <p>Mínimo: {{ resumen_hum.min }}</p>
                <p>Máximo: {{ resumen_hum.max }}</p>
            </div>
        </div>

        <table>
            <tr>
                <th>ID</th>
                <th>Fecha y Hora</th>
                <th>Temperatura</th>
                <th>Presión</th>
                <th>Humedad</th>
            </tr>
            {% for fila in datos %}
            <tr>
                <td>{{ fila[0] }}</td>
                <td>{{ fila[1] }}</td>
                <td class="{% if fila[2] < 20 or fila[2] > 25 %}alerta{% endif %}">{{ "%.2f"|format(fila[2]) }}</td>
                <td class="{% if fila[3] < 1000 or fila[3] > 1030 %}alerta{% endif %}">{{ "%.2f"|format(fila[3]) }}</td>
                <td class="{% if fila[4] < 30 or fila[4] > 40 %}alerta{% endif %}">{{ "%.2f"|format(fila[4]) }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''

    return render_template_string(html, datos=filas,
                                  resumen_temp=resumen_temp,
                                  resumen_pres=resumen_pres,
                                  resumen_hum=resumen_hum)

# Inicializa y corre el servidor
if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)
