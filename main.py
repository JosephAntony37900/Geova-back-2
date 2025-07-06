import serial
import time
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURACIÓN DEL PUERTO SERIAL ---
BAUDRATE = 115200
PORT = "/dev/serial0"
ser = serial.Serial(PORT, BAUDRATE, timeout=0)

# --- LECTURA DEL SENSOR TF-LUNA ---
def read_tfluna():
    while True:
        if ser.in_waiting >= 9:
            bytes_serial = ser.read(9)
            ser.reset_input_buffer()

            if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:
                distance = bytes_serial[2] + bytes_serial[3] * 256
                strength = bytes_serial[4] + bytes_serial[5] * 256
                temperature = (bytes_serial[6] + bytes_serial[7] * 256) / 8 - 256

                # --- CORRECCIÓN PARA DISTANCIAS MÍNIMAS ---
                if distance >= 20:  # Rechaza valores por debajo de 20 cm
                    return distance, strength, temperature
                else:
                    return None, None, None

# --- GRAFICADO EN TIEMPO REAL ---
def start_plot():
    plt.ion()
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    line, = ax.plot(xdata, ydata, label='Distancia [m]', color='tab:blue')
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Distancia")
    ax.set_ylim(0.2, 8.0)
    ax.set_xlim(0, 30)
    ax.set_title("Lectura en tiempo real - TF-Luna")
    ax.grid(True)
    start_time = time.time()

    while True:
        distance, strength, temperature = read_tfluna()

        if distance:
            now = time.time() - start_time
            meters = round(distance / 100, 2)
            centimeters = distance

            print(f"📏 {centimeters} cm | {meters} m | 🔋 Señal: {strength} | 🌡 Temp: {temperature:.1f} °C")

            xdata.append(now)
            ydata.append(meters)

            if len(xdata) > 300:
                xdata = xdata[1:]
                ydata = ydata[1:]

            line.set_xdata(xdata)
            line.set_ydata(ydata)
            ax.set_xlim(max(0, now - 30), now + 1)
            ax.relim()
            ax.autoscale_view(True, True, False)
            fig.canvas.draw()
            fig.canvas.flush_events()

        time.sleep(0.05)

# --- INICIO DEL PROGRAMA ---
if __name__ == "__main__":
    try:
        print("Iniciando lectura TF-Luna...")
        start_plot()
    except KeyboardInterrupt:
        print("\nLectura interrumpida por el usuario.")
    finally:
        ser.close()
