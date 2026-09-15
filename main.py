from machine import Pin
import network
import time
import ujson
from umqtt.simple import MQTTClient


# =========================================================
# CONFIGURACIÓN DE LOS INTERRUPTORES
# =========================================================

sw1 = Pin(13, Pin.IN, Pin.PULL_DOWN)
sw2 = Pin(12, Pin.IN, Pin.PULL_DOWN)
sw3 = Pin(14, Pin.IN, Pin.PULL_DOWN)
sw4 = Pin(27, Pin.IN, Pin.PULL_DOWN)


# =========================================================
# CONFIGURACIÓN DEL DISPLAY 7 SEGMENTOS
# ÁNODO COMÚN
# =========================================================

A = Pin(15, Pin.OUT)
B = Pin(2, Pin.OUT)
C = Pin(4, Pin.OUT)
D = Pin(5, Pin.OUT)
E = Pin(18, Pin.OUT)
F = Pin(19, Pin.OUT)
G = Pin(21, Pin.OUT)

segmentos = [A, B, C, D, E, F, G]


# =========================================================
# NÚMEROS PARA DISPLAY DE ÁNODO COMÚN
#
# 0 = segmento encendido
# 1 = segmento apagado
# =========================================================

DIGITOS = {
    0: (0, 0, 0, 0, 0, 0, 1),
    1: (1, 0, 0, 1, 1, 1, 1),
    2: (0, 0, 1, 0, 0, 1, 0),
    3: (0, 0, 0, 0, 1, 1, 0),
    4: (1, 0, 0, 1, 1, 0, 0),
    5: (0, 1, 0, 0, 1, 0, 0),
    6: (0, 1, 0, 0, 0, 0, 0),
    7: (0, 0, 0, 1, 1, 1, 1),
    8: (0, 0, 0, 0, 0, 0, 0),
    9: (0, 0, 0, 0, 1, 0, 0)
}

APAGADO = (1, 1, 1, 1, 1, 1, 1)


def mostrar(numero):

    patron = DIGITOS.get(numero, APAGADO)

    for pin, estado in zip(segmentos, patron):
        pin.value(estado)


# =========================================================
# ESTADO DE LOS INTERRUPTORES
#
# b3 = switch 1
# b2 = switch 2
# b1 = switch 3
# b0 = switch 4
# =========================================================

bits = [0, 0, 0, 0]


def calcular_decimal():

    return (
        (bits[0] << 3) |
        (bits[1] << 2) |
        (bits[2] << 1) |
        bits[3]
    )


# =========================================================
# WIFI
# =========================================================

print("Conectando a WiFi...")

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect("Wokwi-GUEST", "")

while not wifi.isconnected():
    time.sleep(0.1)

print("WiFi conectado")
print("IP:", wifi.ifconfig()[0])


# =========================================================
# MQTT
# =========================================================

BROKER = "broker.emqx.io"

TOPIC_PUBLICAR = b"wokwi/esp32/ACA VA EL NOMBRE DEL PROYECTO DE WOKWIK"
TOPIC_RECIBIR = b"wokwi/esp32/parcial_cmd"


# =========================================================
# PUBLICAR ESTADO
# =========================================================

def publicar_estado():

    decimal = calcular_decimal()

    if decimal <= 9:
        mostrar(decimal)
        valor_display = decimal
    else:
        mostrar(-1)
        valor_display = "-"

    mensaje = ujson.dumps({
        "b3": bits[0],
        "b2": bits[1],
        "b1": bits[2],
        "b0": bits[3],
        "decimal": valor_display
    })

    client.publish(TOPIC_PUBLICAR, mensaje)

    print(
        "Switches:",
        bits,
        "Decimal:",
        decimal
    )


# =========================================================
# RECIBIR DATOS DESDE EL HTML
# =========================================================

def recibir_mensaje(topic, mensaje):

    global bits

    try:

        datos = ujson.loads(mensaje)

        bits[0] = int(datos.get("b3", bits[0]))
        bits[1] = int(datos.get("b2", bits[1]))
        bits[2] = int(datos.get("b1", bits[2]))
        bits[3] = int(datos.get("b0", bits[3]))

        print("Comando recibido:", bits)

        publicar_estado()

    except Exception as e:

        print("Error:", e)


# =========================================================
# CONEXIÓN MQTT
# =========================================================

client_id = "ESP32_" + str(time.ticks_ms())

client = MQTTClient(
    client_id,
    BROKER,
    port=1883
)

client.set_callback(recibir_mensaje)

try:

    client.connect()

    print("MQTT conectado")

    client.subscribe(TOPIC_RECIBIR)

    print("Suscrito a:", TOPIC_RECIBIR)

except Exception as e:

    print("Error MQTT:", e)


# =========================================================
# ESTADO INICIAL DE LOS SWITCHES
# =========================================================

switches = [
    sw1.value(),
    sw2.value(),
    sw3.value(),
    sw4.value()
]

bits = list(switches)

publicar_estado()


# =========================================================
# BUCLE PRINCIPAL
# =========================================================

while True:

    try:

        # Revisar si llegó algo desde la página web
        client.check_msg()

        # Leer interruptores físicos
        nuevos_switches = [
            sw1.value(),
            sw2.value(),
            sw3.value(),
            sw4.value()
        ]

        # Detectar cambios físicos
        if nuevos_switches != switches:

            switches = list(nuevos_switches)

            bits = list(nuevos_switches)

            print("Cambio físico:", bits)

            publicar_estado()

        time.sleep(0.05)

    except Exception as e:

        print("Error:", e)

        time.sleep(1)