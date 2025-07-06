import serial
import time
from model import parse_frame
from view import display_data

def main():
    # Puerto UART (en la Pi 5 es el mismo que en la Pi 4)
    port = serial.Serial("/dev/serial0", 115200, timeout=1)

    while True:
        if port.in_waiting >= 9:
            frame = port.read(9)
            data = parse_frame(frame)
            if data:
                display_data(data)
        time.sleep(0.1)  # 10 lecturas por segundo aprox.

if __name__ == "__main__":
    main()
