import psutil

def get_cpu_temperature():
    temperatures = psutil.sensors_temperatures()
    cpu_temperatures = temperatures['coretemp'][0]  # Assuming coretemp is the sensor name
    return cpu_temperatures.current

temperature = get_cpu_temperature()
print(f"CPU Temperature: {temperature} °C")
