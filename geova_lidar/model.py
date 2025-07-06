def parse_frame(frame):
    if frame[0] == 0x59 and frame[1] == 0x59:
        distance_mm = frame[2] + frame[3] * 256
        strength = frame[4] + frame[5] * 256
        temperature = frame[6] + frame[7] * 256
        temp_c = temperature / 8.0 - 256

        distance_cm = distance_mm / 10.0
        distance_m = distance_cm / 100.0 if distance_cm >= 100 else None

        return {
            "distance_mm": distance_mm,
            "distance_cm": distance_cm,
            "distance_m": distance_m,
            "signal_strength": strength,
            "temperature_c": round(temp_c, 2)
        }
    return None
