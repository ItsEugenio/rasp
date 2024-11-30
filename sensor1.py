import RPi.GPIO as GPIO
import time

# Configuración de pines
GPIO.setmode(GPIO.BCM)  # Usamos la numeración BCM de los pines
TRIG = 23              # Pin conectado al TRIG del sensor
ECHO = 24              # Pin conectado al ECHO del sensor

# Configurar los pines como entrada/salida
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def medir_distancia():
    """
    Mide la distancia utilizando el sensor ultrasónico.
    """
    # Asegurarse de que el TRIG esté en bajo
    GPIO.output(TRIG, False)
    time.sleep(0.2)  # Pausa para estabilizar el sensor

    # Enviar un pulso al TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # Pulso de 10 microsegundos
    GPIO.output(TRIG, False)

    # Esperar el inicio de la señal en ECHO
    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    # Esperar el final de la señal en ECHO
    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    # Calcular duración de la señal
    elapsed_time = stop_time - start_time

    # Convertir tiempo en distancia (34300 cm/s es la velocidad del sonido)
    distancia = (elapsed_time * 34300) / 2
    return distancia

try:
    print("Iniciando medición. Presiona Ctrl+C para salir.")
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia:.2f} cm")
        time.sleep(1)  # Esperar 1 segundo entre mediciones

except KeyboardInterrupt:
    print("\nMedición detenida por el usuario.")
    GPIO.cleanup()  # Limpiar los pines GPIO al finalizar
