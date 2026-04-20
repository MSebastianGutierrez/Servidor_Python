#!/usr/bin/env python3
"""
Cliente para el juego de Preguntas y Respuestas
Recibe preguntas del servidor y envía respuestas.
"""

import socket
import sys

# ============================================
# CONFIGURACIÓN DEL CLIENTE
# ============================================
HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 4096

# ============================================
# CLASE CLIENTE PREGUNTAS
# ============================================

class ClientePreguntas:
    """
    Cliente que recibe preguntas del servidor y envía respuestas.
    """
    
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.socket_cliente = None
        self.conectado = False
    
    def conectar(self) -> bool:
        """Establece conexión con el servidor."""
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host, self.port))
            self.conectado = True
            
            # Recibir mensaje de bienvenida
            bienvenida = self.recibir_mensaje()
            if bienvenida:
                print(bienvenida)
            
            return True
            
        except ConnectionRefusedError:
            print(f"\n Error: No se pudo conectar al servidor {self.host}:{self.port}")
            print("   Asegúrate de que el servidor esté ejecutándose")
            return False
        except Exception as e:
            print(f" Error de conexión: {e}")
            return False
    
    def recibir_mensaje(self) -> str:
        """Recibe un mensaje del servidor."""
        try:
            datos = self.socket_cliente.recv(BUFFER_SIZE)
            if not datos:
                return ""
            return datos.decode('utf-8')
        except socket.error:
            self.conectado = False
            return ""
    
    def enviar_mensaje(self, mensaje: str) -> bool:
        """Envía un mensaje al servidor."""
        try:
            self.socket_cliente.sendall(mensaje.encode('utf-8'))
            return True
        except socket.error:
            self.conectado = False
            return False
    
    def ejecutar(self):
        """Bucle principal del cliente."""
        if not self.conectar():
            return
        
        try:
            while self.conectado:
                # Recibir mensaje del servidor (pregunta o resultado)
                mensaje = self.recibir_mensaje()
                
                if not mensaje:
                    print("\n El servidor cerró la conexión")
                    break
                
                # Mostrar mensaje del servidor
                print(mensaje)
                
                # Si el mensaje contiene "conexión cerrada" o "finalizado", salir
                if "conexión cerrada" in mensaje.lower() or "gracias por jugar" in mensaje.lower():
                    break
                
                # Si el mensaje termina con ":", es una pregunta que espera respuesta
                if mensaje.strip().endswith(':'):
                    # Leer respuesta del usuario
                    respuesta = input(" Tu respuesta: ").strip()
                    
                    if not respuesta:
                        continue
                    
                    # Enviar respuesta al servidor
                    if not self.enviar_mensaje(respuesta):
                        print(" Error al enviar respuesta. Conexión perdida.")
                        break
                    
                    # Si el usuario quiere exito
                    if respuesta.lower() == 'exito':
                        # Recibir mensaje de despedida
                        despedida = self.recibir_mensaje()
                        if despedida:
                            print(despedida)
                        break
                
        except KeyboardInterrupt:
            print("\n Conexión interrumpida por el usuario")
        finally:
            self.desconectar()
    
    def desconectar(self):
        """Cierra la conexión con el servidor."""
        if self.socket_cliente:
            self.socket_cliente.close()
        print(" Conexión cerrada")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    host = HOST
    port = PORT
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    cliente = ClientePreguntas(host, port)
    cliente.ejecutar()

if __name__ == "__main__":
    main()