from gpiozero import DistanceSensor
import socketio
import time
import requests
from datetime import datetime
import pytz
import statistics
import threading

# Configuración del WebSocket
websocket_url = 'http://54.198.117.11'  # URL del servidor WebSocket
sio = socketio.Client()

# Configuración del sensor ultrasónico
sensor = DistanceSensor(echo=24, trigger=23, max_distance=6)  # Rango de 6 metros

# Variables de conteo de personas
personas_contadas = 0
ventana_lecturas = []  # Para almacenar lecturas recientes
persona_deteccionada = False
DEBOUNCE_TIME = 0.5  # Pausa entre mediciones
ultimo_envio_post = time.time()  # Para manejar el envío POST cada hora

# Lock para proteger el acceso a `personas_contadas`
personas_lock = threading.Lock()

# Función para enviar mensaje al WebSocket
def enviar_websocket():
    try:
        sio.connect(websocket_url)
        # Leer `personas_contadas` de forma segura dentro del Lock
        with personas_lock:
            sio.emit('personasDentro', personas_contadas)
        print("Mensaje enviado al WebSocket")
        sio.disconnect()
    except Exception as e:
        print(f"Error al enviar mensaje al WebSocket: {e}")

# Función para enviar la petición POST con datos en formato JSON
def enviar_peticion_post():
    global personas_contadas
    # Configuración de la zona horaria
    timezone = pytz.timezone("America/Mexico_City")
    now = datetime.now(timezone)

    # Leer `personas_contadas` de forma segura dentro del Lock
    with personas_lock:
        registro_personas_adentro = {
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:00"),
            "numero_personas": personas_contadas,
            "lugar": "adentro",
            "idKit": 12345
        }
        # Reiniciar el contador después de enviar el POST
        personas_contadas = 0

    # Configuración de la solicitud POST
    api_url = 'http://107.23.14.43/registro'
    headers = {'Content-Type': 'application/json'}

    try:
        # Enviar la solicitud POST
        response = requests.post(api_url, headers=headers, json=registro_personas_adentro)
        if response.status_code == 200:
            print("Petición POST enviada exitosamente.")
        else:
            print(f"Error en la solicitud POST: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error al enviar la petición POST: {e}")

# Función para analizar lecturas y detectar personas
def detectar_persona(distancia):
    global ventana_lecturas, personas_contadas, persona_deteccionada

    # Almacenar la lectura actual en la ventana deslizante
    ventana_lecturas.append(distancia)
    if len(ventana_lecturas) > 2:  # Mantener un historial de las últimas 10 lecturas
        ventana_lecturas.pop(0)

    # Analizar los cambios en la ventana
    if len(ventana_lecturas) >= 2:
        cambio_max = max(ventana_lecturas) - min(ventana_lecturas)
        desviacion = statistics.stdev(ventana_lecturas)

        # Detectar movimiento humano: Cambios significativos y estables
        if cambio_max > 30 and desviacion > 5 and not persona_deteccionada:
            persona_deteccionada = True
            with personas_lock:
                personas_contadas += 1
            print(f"¡Persona detectada! Número de personas contadas: {personas_contadas}")
            enviar_websocket()

        # Restablecer cuando no hay más cambios
        if cambio_max < 2 and persona_deteccionada:
            persona_deteccionada = False
            print("Persona salió del área de detección.")

# Función para monitorear el sensor de distancia
def monitorizar_distancia():
    while True:
        # Obtener una lectura de distancia
        distancia = sensor.distance * 100  # Convertir a centímetros
        print(f"Distancia detectada: {distancia:.2f} cm")

        # Llamar a la función de detección
        detectar_persona(distancia)

        # Pausa entre mediciones
        time.sleep(DEBOUNCE_TIME)

# Función para enviar los datos cada hora
def enviar_datos_cada_hora():
    global ultimo_envio_post
    while True:
        if time.time() - ultimo_envio_post >= 3600:  # Si ha pasado una hora
            enviar_peticion_post()
            ultimo_envio_post = time.time()  # Actualizar el tiempo del último envío
        time.sleep(60)  # Comprobar cada minuto si ya ha pasado 1 hora

# Función principal para iniciar los hilos
def main():
    # Crear hilos para tareas concurrentes
    hilo_sensor = threading.Thread(target=monitorizar_distancia)
    hilo_post = threading.Thread(target=enviar_datos_cada_hora)

    # Iniciar los hilos
    hilo_sensor.start()
    hilo_post.start()

    # Mantener el programa principal corriendo
    hilo_sensor.join()
    hilo_post.join()

# Ejecutar la función principal
if __name__ == "__main__":
    main()
