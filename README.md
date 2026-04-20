# Servidor de Juego de Preguntas y Respuestas con Python y SQLite

## Descripcion

Este proyecto implementa un servidor de juego de preguntas y respuestas para la materia Programacion en Redes.

Base del desarrollo: Partiendo del ejemplo de chat basico visto en clase (servidor que recibe mensajes, los guarda en SQLite y responde con timestamp), extiendo la funcionalidad para crear un juego interactivo donde el servidor hace preguntas al cliente, evalua respuestas y lleva puntaje.

Trabajo Practico - 1er Cuatrimestre 2026

## Funcionalidades

## Servidor (server.py)

- Escucha en localhost:5000
- Acepta multiples clientes simultaneos (usando threading)
- Tiene 15 preguntas predefinidas sobre cultura general, matematica y programacion
- Evalua respuestas (sin distinguir mayusculas/minusculas)
- Guarda cada respuesta en SQLite con campos: id, pregunta, respuesta_cliente, es_correcta, ip_cliente, fecha_envio
- Lleva puntaje en vivo durante la partida
- Muestra estadisticas globales al finalizar
- Manejo de errores (puerto ocupado, DB no accesible)
- Logging completo de operaciones
- Codigo modular con clases separadas

## Cliente (client.py)

- Se conecta al servidor en localhost:5000
- Recibe preguntas del servidor y envia respuestas
- Permite escribir "exito" para terminar el juego
- Muestra feedback inmediato (correcto/incorrecto)
- Soporta argumentos de linea de comandos

## Conceptos Aplicados (desde el ejemplo de clase)

- Sockets TCP/IP: Comunicacion cliente-servidor
- SQLite: Persistencia de respuestas
- Threading: Multiples clientes simultaneos
- Logging: Registro de eventos del servidor
- Manejo de señales: Ctrl+C para cierre limpio
- Manejo de errores: Puerto ocupado, DB inaccesible

Extension propia: Añadi logica de juego (preguntas, evaluacion, puntaje) manteniendo la misma arquitectura del ejemplo.

## Estructura de la Base de Datos

CREATE TABLE respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pregunta TEXT NOT NULL,
    respuesta_cliente TEXT NOT NULL,
    es_correcta INTEGER NOT NULL,
    ip_cliente TEXT NOT NULL,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP
);

## Lista de Preguntas (15)

1. Cual es la capital de Francia? -> paris
2. Cual es la capital de Argentina? -> buenos aires
3. Cual es la capital de España? -> madrid
4. Cual es la capital de Brasil? -> brasilia
5. Cual es la capital de Mexico? -> ciudad de mexico
6. Cual es la capital de Italia? -> roma
7. Cual es la capital de Alemania? -> berlin
8. Cuantos lados tiene un cuadrado? -> 4
9. Cuanto es 2 + 2? -> 4
10. Cuanto es 5 * 6? -> 30
11. Que lenguaje de programacion usamos? -> python
12. Que es un socket? -> un punto final para comunicacion
13. Que significa SQL? -> structured query language
14. En que año llego el hombre a la luna? -> 1969
15. Quien pinto la Mona Lisa? -> leonardo da vinci

## Instalacion y Ejecucion

Requisitos Previos:
- Python 3.6 o superior
- No requiere librerias externas

Pasos:

1. Clonar el repositorio:
   git clone https://github.com/MSebastianGutierrez/Servidor_Python.git
   cd Servidor_Python

2. Iniciar el servidor (Primera terminal):
   python server.py

3. Iniciar un cliente (Segunda terminal):
   python client.py

4. Jugar:
   - El servidor hara preguntas una por una
   - Escribe tu respuesta y presiona Enter
   - Escribe "exito" para salir

## Estructura del Proyecto

Servidor_Python/
├── server.py          # Servidor con juego de preguntas
├── client.py          # Cliente interactivo
├── mensajes.db        # Base de datos SQLite (se crea automaticamente)
└── README.md          # Documentacion

## Arquitectura del Codigo

Clases principales:

- DatabaseManager: Gestiona conexion a SQLite, guarda respuestas, obtiene estadisticas
- ManejadorCliente: Atiende un cliente especifico (hilo independiente)
- ServidorPreguntas: Acepta conexiones y crea hilos para cada cliente

## Manejo de Errores

- Puerto 5000 ocupado: Servidor muestra error y termina
- DB no accesible: Servidor muestra error y no acepta conexiones
- Servidor no disponible: Cliente muestra "No se pudo conectar"
- Cliente se desconecta abruptamente: Servidor lo detecta y continua
- Respuesta vacia: Cliente la ignora
- Ctrl+C en servidor: Cierra conexiones limpiamente

## Mejoras respecto al ejemplo de clase

Ejemplo de clase:
- Chat simple
- Guarda mensajes
- Responde con timestamp

Mi implementacion:
- Juego de preguntas y respuestas
- Guarda preguntas + respuestas + evaluacion
- Responde con feedback + puntaje
- 15 preguntas predefinidas
- Evaluacion de respuestas
- Puntaje en vivo
- Estadisticas finales

## Licencia

Proyecto academico - Libre para uso educativo
