# Proyecto de Redes

Este proyecto consiste en un sistema distribuido heterogéneo que simula un entorno **IoT industrial**, permitiendo la transmisión, almacenamiento, consulta y visualización de datos de series de tiempo entre **C++** y **Python**, utilizando **sockets TCP** para la comunicacióñ binaria y **HTTP** para la API. El sistema emplea una **base de datos local** para persistencia y cumple requisitos de seguridad, tolerancia a fallos y visualización en tiempo real.

## Estructura del proyecto

```bash
.
├── módulo1-cliente-sensor/
│   └── ClienteSensor.exe
├── módulo2-servidor-intermedio/
│   └── servidor_intermedio.py
├── módulo3-servidor-final/
│   └── servidor_final.py
└── módulo4_cliente_consulta/
    └── cliente_consulta.py
```

## Ejecución
Debes ejecutar los componentes en el siguiente orden, cada uno en una terminal separada:

1. **Servidor Final**

```bash
python módulo3-servidor-final/servidor_final.py
```

Una vez ejecutado puedes acceder al dashboard entrando [aqui](http://localhost:5000/dashboard). 

2. **Servidor Intermedio**

```bash
python módulo2-servidor-intermedio/servidor_intermedio.py
```

3. **Cliente Sensor**

```bash
./módulo1-cliente-sensor/ClienteSensor.exe
```
4. **Cliente de Consulta**

```bash
python módulo4_cliente_consulta/cliente_consulta.py
```

Asegúrate de que los servidores estén escuchando antes de iniciar el cliente sensor.

# Biblioteca OpenSSL necesaria

Para poder utilizar ClienteSensor.cpp es necesario instalar Win64 OpenSSL v3.5.0 EXE en la pagina siguiente https://slproweb.com/products/Win32OpenSSL.html
