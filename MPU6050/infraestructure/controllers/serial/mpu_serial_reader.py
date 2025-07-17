import smbus
import time

class MPUSerialReader:
    def __init__(self, bus=1, address=0x68):
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.bus.write_byte_data(self.address, 0x6B, 0)  # Wake up

    def read(self):
        def read_word(reg):
            h = self.bus.read_byte_data(self.address, reg)
            l = self.bus.read_byte_data(self.address, reg + 1)
            value = (h << 8) + l
            return value - 65536 if value >= 0x8000 else value

        try:
            ax = read_word(0x3B) / 16384.0
            ay = read_word(0x3D) / 16384.0
            az = read_word(0x3F) / 16384.0
            gx = read_word(0x43) / 131.0
            gy = read_word(0x45) / 131.0
            gz = read_word(0x47) / 131.0

            return {
                "ax": round(ax, 2),
                "ay": round(ay, 2),
                "az": round(az, 2),
                "gx": round(gx, 2),
                "gy": round(gy, 2),
                "gz": round(gz, 2)
            }
        except:
            return None
