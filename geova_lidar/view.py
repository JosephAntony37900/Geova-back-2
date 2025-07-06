def display_data(data):
    print("------------ LIDAR DATA ------------")
    print(f"Distancia: {data['distance_mm']} mm | {data['distance_cm']} cm", end="")
    if data['distance_m']:
        print(f" | {round(data['distance_m'], 2)} m")
    else:
        print()
    print(f"Fuerza de señal: {data['signal_strength']}")
    print(f"Temperatura interna: {data['temperature_c']} °C")
    print("------------------------------------\n")
