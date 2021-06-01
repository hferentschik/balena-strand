import datetime
import json
import os
import time

import paho.mqtt.client as mqtt

from pijuice import PiJuice
from balena import Balena

from datetime import datetime, timedelta
from dateutil.tz import tzutc
from time import sleep
from w1thermsensor import W1ThermSensor

WAKEALARM = '/sys/class/rtc/rtc0/wakealarm'
BROKER_ADDRESS = os.environ.get('MQTT_BROKER') or "mqtt"
BROKER_PORT = os.environ.get('MQTT_BROKER_PORT') or 80
SLEEP_INTERVAL = os.environ.get('SLEEP_INTERVAL') or 60
STAY_ALIVE = os.environ.get('STAY_ALIVE') or False


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


def update_tag(tag, variable):
    """Set a tag for the Balena device."""
    balena.models.tag.device.set(os.environ['BALENA_DEVICE_UUID'], str(tag), str(variable))


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
        update_tag("WAKEUP_TIME", wakeup_time.strftime("%Y-%m-%d %H:%M:%S"))
    except OSError as e:
        print('Error setting wake alarm: %s' % e)


def record_temperature():
    """Record current temperature and send to MQTT broker."""
    sensor = W1ThermSensor()
    temperature = sensor.get_temperature()
    update_tag("TEMPERATURE", temperature)
    client = mqtt.Client(transport="websockets")
    client.connect(BROKER_ADDRESS, 80)
    json_body = [
        {
            "time": str('{:%Y-%m-%dT%H:%M:%S}'.format(datetime.now(tzutc()))),
            "measurement": "water-temperature",
            "fields": {
                "temperature": temperature,
                "sensor": "DS18B20"
            }
        }
    ]

    print("JSON body = " + str(json_body))
    msg_info = client.publish("sensors", json.dumps(json_body))
    if not msg_info.is_published():
        msg_info.wait_for_publish()
    client.disconnect()


def stay_alive(pj):
    """Enter endless loop recording temperature."""
    while True:
        record_temperature()

        battery_data = get_battery_parameters(pj)
        print(battery_data)
        for key, value in battery_data.items():
            update_tag(key, value)

        sleep(60)


def shutdown(pj):
    """Shutdown Pi."""
    shutdown_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_tag("SHUTDOWN_TIME", shutdown_time)
    set_alarm(SLEEP_INTERVAL)
    pj.power.SetPowerOff(60)

    balena.models.supervisor.shutdown(device_uuid=os.environ['BALENA_DEVICE_UUID'],
                                      app_id=os.environ['BALENA_APP_ID'])


# Start the SDK and record start tag
balena = Balena()
balena.auth.login_with_token(os.environ['BALENA_API_KEY'])
update_tag("START_TIME", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Wait for device I2C device to start
while not os.path.exists('/dev/i2c-1'):
    print("Waiting to identify PiJuice")
    time.sleep(0.1)

# Initiate PiJuice and make sure watchdog is disabled
pi_juice = PiJuice(1, 0x14)
pi_juice.power.SetWatchdog(0)

if STAY_ALIVE == '1':
    stay_alive(pi_juice)

record_temperature()
shutdown(pi_juice)
