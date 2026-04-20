#!/usr/bin/env python3
"""
Servidor de Preguntas y Respuestas
Hace preguntas al cliente, evalúa respuestas y guarda el historial en SQLite.
"""

import socket
import sqlite3
import threading
import logging
import signal
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN DEL SERVIDOR
# ============================================
HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 4096
MAX_CLIENTES = 10
DB_FILE = 'mensajes.db'

# ============================================
# BASE DE PREGUNTAS Y RESPUESTAS CORRECTAS
# ============================================
PREGUNTAS = [
    {"pregunta": "¿Cuál es la capital de Francia?", "respuesta_correcta": "paris"},
    {"pregunta": "¿Cuál es la capital de Argentina?", "respuesta_correcta": "buenos aires"},
    {"pregunta": "¿Cuál es la capital de España?", "respuesta_correcta": "madrid"},
    {"pregunta": "¿Cuál es la capital de Brasil?", "respuesta_correcta": "brasilia"},
    {"pregunta": "¿Cuál es la capital de México?", "respuesta_correcta": "ciudad de méxico"},
    {"pregunta": "¿Cuál es la capital de Italia?", "respuesta_correcta": "roma"},
    {"pregunta": "¿Cuál es la capital de Alemania?", "respuesta_correcta": "berlín"},
    {"pregunta": "¿Cuántos lados tiene un cuadrado?", "respuesta_correcta": "4"},
    {"pregunta": "¿Cuánto es 2 + 2?", "respuesta_correcta": "4"},
    {"pregunta": "¿Cuánto es 5 * 6?", "respuesta_correcta": "30"},
    {"pregunta": "¿Qué lenguaje de programación usamos?", "respuesta_correcta": "python"},
    {"pregunta": "¿Qué es un socket?", "respuesta_correcta": "un punto final para comunicación entre procesos"},
    {"pregunta": "¿Qué significa SQL?", "respuesta_correcta": "structured query language"},
    {"pregunta": "¿En qué año llegó el hombre a la luna?", "respuesta_correcta": "1969"},
    {"pregunta": "¿Quién pintó la Mona Lisa?", "respuesta_correcta": "leonardo da vinci"},
]

# ============================================
# CLASE MANEJADOR DE BASE DE DATOS
# ============================================

class DatabaseManager:
    """
    Gestiona todas las operaciones con la base de datos SQLite.
    """
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.lock = threading.Lock()
        self._inicializar_db()
    
    def _inicializar_db(self):
        """Crea la tabla si no existe."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS respuestas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pregunta TEXT NOT NULL,
                        respuesta_cliente TEXT NOT NULL,
                        es_correcta INTEGER NOT NULL,
                        ip_cliente TEXT NOT NULL,
                        fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info(f" Base de datos inicializada: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f" Error al inicializar la base de datos: {e}")
            raise
    
    def guardar_respuesta(self, pregunta: str, respuesta: str, es_correcta: bool, ip_cliente: str) -> Optional[int]:
        """
        Guarda una respuesta en la base de datos.
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO respuestas (pregunta, respuesta_cliente, es_correcta, ip_cliente, fecha_envio)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (pregunta, respuesta, 1 if es_correcta else 0, ip_cliente, datetime.now().isoformat()))
                    conn.commit()
                    respuesta_id = cursor.lastrowid
                    logger.info(f" Respuesta guardada [ID:{respuesta_id}] - Correcta: {es_correcta}")
                    return respuesta_id
        except sqlite3.Error as e:
            logger.error(f" Error al guardar respuesta: {e}")
            return None
    
    def obtener_estadisticas(self, ip_cliente: str) -> dict:
        """Obtiene estadísticas del cliente."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*), SUM(es_correcta) 
                    FROM respuestas 
                    WHERE ip_cliente = ?
                ''', (ip_cliente,))
                total, correctas = cursor.fetchone()
                
                total = total or 0
                correctas = correctas or 0
                
                return {
                    'total': total,
                    'correctas': correctas,
                    'incorrectas': total - correctas,
                    'porcentaje': (correctas / total * 100) if total > 0 else 0
                }
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'correctas': 0, 'incorrectas': 0, 'porcentaje': 0}

# ============================================
# CLASE MANEJADOR DE CLIENTE
# ============================================

class ManejadorCliente:
    """
    Maneja la comunicación con un cliente individual.
    El servidor hace preguntas y el cliente responde.
    """
    
    def __init__(self, conexion: socket.socket, direccion: Tuple[str, int], 
                 db_manager: DatabaseManager, cliente_id: int):
        self.conexion = conexion
        self.direccion = direccion
        self.ip_cliente = direccion[0]
        self.puerto_cliente = direccion[1]
        self.db_manager = db_manager
        self.cliente_id = cliente_id
        self.conectado = True
        self.indice_pregunta = 0
        self.puntaje = 0
        self.total_preguntas = len(PREGUNTAS)
        
        logger.info(f" Cliente #{cliente_id} conectado desde {self.ip_cliente}:{self.puerto_cliente}")
    
    def enviar_mensaje(self, mensaje: str) -> bool:
        """Envía un mensaje al cliente."""
        try:
            self.conexion.sendall(mensaje.encode('utf-8'))
            return True
        except (socket.error, BrokenPipeError) as e:
            logger.warning(f" Cliente #{self.cliente_id}: Error al enviar: {e}")
            self.conectado = False
            return False
    
    def recibir_mensaje(self) -> Optional[str]:
        """Recibe un mensaje del cliente."""
        try:
            datos = self.conexion.recv(BUFFER_SIZE)
            if not datos:
                return None
            return datos.decode('utf-8').strip()
        except socket.error as e:
            logger.warning(f" Cliente #{self.cliente_id}: Error al recibir: {e}")
            return None
    
    def normalizar_respuesta(self, respuesta: str) -> str:
        """Normaliza la respuesta para comparación (minúsculas, sin espacios extra)."""
        return respuesta.strip().lower()
    
    def verificar_respuesta(self, respuesta: str, respuesta_correcta: str) -> bool:
        """Verifica si la respuesta es correcta (con tolerancia)."""
        respuesta_norm = self.normalizar_respuesta(respuesta)
        correcta_norm = self.normalizar_respuesta(respuesta_correcta)
        
        # Comparación exacta
        if respuesta_norm == correcta_norm:
            return True
        
        # Comparación con tolerancia (ej: "buenos aires" vs "buenos Aires")
        if respuesta_norm in correcta_norm or correcta_norm in respuesta_norm:
            return True
        
        return False
    
    def mostrar_pregunta(self):
        """Muestra la pregunta actual al cliente."""
        if self.indice_pregunta < self.total_preguntas:
            pregunta_actual = PREGUNTAS[self.indice_pregunta]
            mensaje = (
                f"\n{'='*50}\n"
                f" PREGUNTA {self.indice_pregunta + 1} de {self.total_preguntas}\n"
                f"{'='*50}\n"
                f" {pregunta_actual['pregunta']}\n"
                f"{'='*50}\n"
                f" Escribe tu respuesta (o 'exito' para terminar):\n"
            )
            self.enviar_mensaje(mensaje)
        else:
            self.finalizar_juego()
    
    def finalizar_juego(self):
        """Finaliza el juego y muestra el puntaje final."""
        porcentaje = (self.puntaje / self.total_preguntas * 100) if self.total_preguntas > 0 else 0
        
        # Guardar estadísticas finales
        stats = self.db_manager.obtener_estadisticas(self.ip_cliente)
        
        mensaje_final = (
            f"\n{'='*50}\n"
            f"🏆 JUEGO FINALIZADO\n"
            f"{'='*50}\n"
            f" Tu puntaje: {self.puntaje} / {self.total_preguntas}\n"
            f" Porcentaje: {porcentaje:.1f}%\n"
            f"{'='*50}\n"
            f" Estadísticas totales:\n"
            f"   • Respuestas totales: {stats['total']}\n"
            f"   • Correctas: {stats['correctas']}\n"
            f"   • Incorrectas: {stats['incorrectas']}\n"
            f"   • Porcentaje global: {stats['porcentaje']:.1f}%\n"
            f"{'='*50}\n"
            f" ¡Gracias por jugar! Conexión cerrada.\n"
        )
        self.enviar_mensaje(mensaje_final)
        self.conectado = False
    
    def manejar(self):
        """
        Bucle principal: el servidor hace preguntas y el cliente responde.
        """
        # Mensaje de bienvenida
        bienvenida = (
            f"\n{'='*50}\n"
            f" BIENVENIDO AL JUEGO DE PREGUNTAS Y RESPUESTAS\n"
            f" Cliente #{self.cliente_id}\n"
            f" IP: {self.ip_cliente}:{self.puerto_cliente}\n"
            f"{'='*50}\n"
            f" El servidor te hará {self.total_preguntas} preguntas.\n"
            f" Responde correctamente para sumar puntos.\n"
            f" Escribe 'exito' en cualquier momento para terminar.\n"
            f"{'='*50}\n"
            f"¡Buena suerte!\n"
        )
        self.enviar_mensaje(bienvenida)
        
        # Comenzar con la primera pregunta
        self.mostrar_pregunta()
        
        while self.conectado and self.indice_pregunta < self.total_preguntas:
            # Recibir respuesta del cliente
            respuesta = self.recibir_mensaje()
            
            if respuesta is None:
                break
            
            if not respuesta:
                continue
            
            logger.info(f" Cliente #{self.cliente_id} respondió: {respuesta}")
            
            # Comando para salir
            if respuesta.lower() == 'exito':
                self.enviar_mensaje(" ¡Hasta luego! Gracias por participar.")
                break
            
            # Verificar respuesta
            pregunta_actual = PREGUNTAS[self.indice_pregunta]
            es_correcta = self.verificar_respuesta(respuesta, pregunta_actual['respuesta_correcta'])
            
            # Guardar en base de datos
            self.db_manager.guardar_respuesta(
                pregunta_actual['pregunta'],
                respuesta,
                es_correcta,
                self.ip_cliente
            )
            
            # Actualizar puntaje
            if es_correcta:
                self.puntaje += 1
                mensaje_resultado = f" ¡CORRECTO! +1 punto. Puntaje actual: {self.puntaje}/{self.indice_pregunta + 1}"
            else:
                mensaje_resultado = (
                    f" INCORRECTO. La respuesta correcta era: '{pregunta_actual['respuesta_correcta']}'\n"
                    f" Puntaje actual: {self.puntaje}/{self.indice_pregunta + 1}"
                )
            
            self.enviar_mensaje(mensaje_resultado)
            
            # Avanzar a la siguiente pregunta
            self.indice_pregunta += 1
            
            # Mostrar siguiente pregunta si hay más
            if self.indice_pregunta < self.total_preguntas:
                self.mostrar_pregunta()
            else:
                self.finalizar_juego()
        
        # Cerrar conexión
        self.conexion.close()
        logger.info(f" Cliente #{self.cliente_id} desconectado - Puntaje final: {self.puntaje}/{self.total_preguntas}")

# ============================================
# CLASE SERVIDOR PRINCIPAL
# ============================================

class ServidorPreguntas:
    """
    Servidor principal que acepta conexiones y crea hilos para cada cliente.
    """
    
    def __init__(self, host: str = HOST, port: int = PORT, max_clientes: int = MAX_CLIENTES):
        self.host = host
        self.port = port
        self.max_clientes = max_clientes
        self.db_manager = DatabaseManager()
        self.socket_servidor = None
        self.contador_clientes = 0
        self.running = True
        
        signal.signal(signal.SIGINT, self._manejar_senal)
        signal.signal(signal.SIGTERM, self._manejar_senal)
    
    def _manejar_senal(self, signum, frame):
        logger.info(f" Señal {signum} recibida, cerrando servidor...")
        self.running = False
    
    def inicializar_socket(self) -> bool:
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen(self.max_clientes)
            self.socket_servidor.settimeout(1.0)
            
            logger.info(f" Servidor de preguntas iniciado")
            logger.info(f" Escuchando en {self.host}:{self.port}")
            logger.info(f" Total de preguntas: {len(PREGUNTAS)}")
            logger.info(f" Base de datos: {DB_FILE}")
            logger.info("=" * 50)
            logger.info("Presiona Ctrl+C para detener el servidor")
            logger.info("=" * 50)
            
            return True
            
        except socket.error as e:
            if e.errno == 98 or e.errno == 10048:
                logger.error(f" Error: El puerto {self.port} ya está en uso")
            else:
                logger.error(f" Error al inicializar el socket: {e}")
            return False
    
    def aceptar_conexiones(self):
        while self.running:
            try:
                conexion, direccion = self.socket_servidor.accept()
                self.contador_clientes += 1
                
                manejador = ManejadorCliente(
                    conexion, 
                    direccion,
                    self.db_manager,
                    self.contador_clientes
                )
                
                hilo_cliente = threading.Thread(
                    target=manejador.manejar,
                    daemon=True
                )
                hilo_cliente.start()
                
                logger.info(f" Cliente #{self.contador_clientes} asignado al hilo {hilo_cliente.name}")
                
            except socket.timeout:
                continue
            except socket.error as e:
                if self.running:
                    logger.error(f"Error aceptando conexión: {e}")
            except Exception as e:
                if self.running:
                    logger.error(f"Error inesperado: {e}")
    
    def iniciar(self):
        if not self.inicializar_socket():
            return
        
        try:
            self.aceptar_conexiones()
        except KeyboardInterrupt:
            logger.info("\n Servidor detenido por el usuario")
        finally:
            self.detener()
    
    def detener(self):
        self.running = False
        if self.socket_servidor:
            self.socket_servidor.close()
        logger.info(" Servidor cerrado correctamente")

# ============================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================

if __name__ == "__main__":
    servidor = ServidorPreguntas()
    servidor.iniciar()