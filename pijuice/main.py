import datetime
import os
import requests
import time

from balena import Balena
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from pijuice import PiJuice
from time import sleep
from w1thermsensor import W1ThermSensor

WAKEALARM = '/sys/class/rtc/rtc0/wakealarm'
API_ENDPOINT = os.environ.get('API_ENDPOINT') or "http://lora:8080/api/v1/send"
SLEEP_INTERVAL = os.environ.get('SLEEP_INTERVAL') or 60

def get_battery_parameters(pj):
    """Get all PiJuice parameters and return as a dictionary"""
    juice = {}

    charge = pj.status.GetChargeLevel()
    juice['charge'] = charge['data'] if charge['error'] == 'NO_ERROR' else charge['error']

    # Temperature [C]
    temperature = pj.status.GetBatteryTemperature()
    juice['temperature'] = temperature['data'] if temperature['error'] == 'NO_ERROR' else temperature['error']

    # Battery voltage  [V]
    vbat = pj.status.GetBatteryVoltage()
    juice['vbat'] = vbat['data'] / 1000 if vbat['error'] == 'NO_ERROR' else vbat['error']

    # Battery current [A]
    ibat = pj.status.GetBatteryCurrent()
    juice['ibat'] = ibat['data'] / 1000 if ibat['error'] == 'NO_ERROR' else ibat['error']

    # I/O voltage [V]
    vio = pj.status.GetIoVoltage()
    juice['vio'] = vio['data'] / 1000 if vio['error'] == 'NO_ERROR' else vio['error']

    # I/O current [A]
    iio = pj.status.GetIoCurrent()
    juice['iio'] = iio['data'] / 1000 if iio['error'] == 'NO_ERROR' else iio['error']

    # Get power input (if power connected to the PiJuice board)
    status = pj.status.GetStatus()
    juice['power_input'] = status['data']['powerInput'] if status['error'] == 'NO_ERROR' else status['error']

    # Get power input (if power connected to the Raspberry Pi board)
    status = pj.status.GetStatus()
    juice['power_input_board'] = status['data']['powerInput5vIo'] if status['error'] == 'NO_ERROR' else status['error']

    return juice

def set_alarm(interval):
    """Set upcoming wakealarm."""
    wakeup_time = datetime.now() + timedelta(minutes=int(interval))
    timestamp = '{0:.0f}\n'.format(wakeup_time.timestamp())
    try:
        with open(WAKEALARM, 'w') as f:
            f.write('0\n')
        with open(WAKEALARM, 'w') as f:
            f.write(timestamp)
        print('Wakealarm set to: %s' % wakeup_time)
    except OSError as e:
        print('Error setting wake alarm: %s' % e)

def record(pj):
    record_temperature()
    record_charge(pj)

def record_temperature():
    """Record current temperature and send to MQTT broker."""
    sensor = W1ThermSensor()
    temperature = sensor.get_temperature()
    payload = [
        {
            "time": str('{:%Y-%m-%dT%H:%M:%S}'.format(datetime.now(tzutc()))),
            "measurement": "water-temperature",
            "fields": {
                "temperature": temperature,
                "sensor": "DS18B20"
            }
        }
    ]
    send(payload)

def record_charge(pj):
    """Record the PiJuice charge level."""

    charge = pj.status.GetChargeLevel().get('data')
    payload = [
        {
            "time": str('{:%Y-%m-%dT%H:%M:%S}'.format(datetime.now(tzutc()))),
            "measurement": "charge",
            "fields": {
                "charge": charge,
            }
        }
    ]
    send(payload)

def send(json):
    print("Sending payload: " + str(json))

    MAX_RETRIES = 5
    for _ in range(MAX_RETRIES):
        response = requests.post(url = API_ENDPOINT, json = json)

        print(response.content.decode("utf-8"))
        if response.ok:
            break
        else:
            sleep(5)

def stay_alive(pj):
    """Enter endless loop recording temperature."""
    while True:
        sleep(300)
        record(pj)


def shutdown(pj):
    """Shutdown Pi."""
    set_alarm(SLEEP_INTERVAL)
    pj.power.SetPowerOff(60)

    balena = Balena()
    balena.models.supervisor.shutdown(device_uuid=os.environ['BALENA_DEVICE_UUID'],
                                      app_id=os.environ['BALENA_APP_ID'])


# Wait for device I2C device to start
while not os.path.exists('/dev/i2c-1'):
    print("Waiting to identify PiJuice")
    time.sleep(0.1)

# Initiate PiJuice and make sure watchdog is disabled
pj = PiJuice(1, 0x14)
pj.power.SetWatchdog(0)

record(pj)

# If 5V power is connected stay alive, else shutdown
if pj.status.GetStatus()["data"]["powerInput5vIo"] != "NOT_PRESENT":
    print("5V Power connected. Staying alive")
    stay_alive(pj)
else:
    print("No external power supply. Set timer and shutdown.")
    shutdown(pj)
