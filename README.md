# Balena Strand

A Balena project using a Raspberry Pi with a [PiJuice](https://github.com/PiSupply/PiJuice) and a DS18B20 1-wire temperature sensor to measure water temperature.
The idea is to have a setup where the Pi wakes up at a given interval, measures the temperature and writes it to a MQTT message queue.
Afterwards the Pi shuts down again.
Internet connectivity is given via a USB dongle.
Using the PiJuice and the solar panel which comes with it, we should be able to take measurements every few hours without being connected to power.

This is a sister project to [balena-weather](https://github.com/hferentschik/balena-weather).

## Balena config

### Device configuration

In order to use the Pijuice real time clock (RTC) and the one wire temperature sensor the following DT overlays must be set:

```sh
"i2c-rtc,ds3231,wakeup-source","w1-gpio,gpiopin=17"
```

*NOTE*: This uses the non default GPIO pin 17 (opposed to 4).

### Device service variables

| Variable  | Description  | Values |
|------------------|-----------------------------------------|------------|
| MQTT_BROKER      | MQTT server name                        | localhost  |
| MQTT_BROKER_PORT | MQTT web-socket port                    | 80         |
| SLEEP_INTERVAL   | Time between measurements               | 60         |
| START_SSHD       | Whether to open SSH port                | [0&vert;1] |
| STAY_ALIVE       | Whether to stay alive after measurement | [0&vert;1] |

## Development

In order to test the code easily, the container uses a trick to allow using [PyCharm](https://www.jetbrains.com/pycharm/) locally and execute the code in the remote container.
For that the container needs to open an SSH port. 
This can be achieved setting the device service variable `START_SSHD=1`.
This will start sshd and allow PyCharm to use the container as a remote execution environment.

*NOTE*: This is a development trick/hack.
In a production environment the sshd config should be removed.

## Misc

* [Balena SDK](https://www.balena.io/docs/reference/sdk/python-sdk/)
* [Pi Juice Getting Started](https://learn.pi-supply.com/make/pijuice-quick-start-guide-faq/)
* [PiJuice Battery Discharge Time Calculator](https://learn.pi-supply.com/battery-levels/)
* [RTC](https://github.com/PiSupply/PiJuice/issues/273)
* [Wakeup via API](https://github.com/PiSupply/PiJuice/issues/216)
* [wakealarm](https://github.com/OpenMediaVault-Plugin-Developers/openmediavault-wakealarm/blob/master/usr/sbin/wakealarm)
