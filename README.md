# Balena Strand

A Balena project using a Raspberry Pi with a [PiJuice](https://github.com/PiSupply/PiJuice) and a DS18B20 1-wire temperature sensor to measure water temperature.
The idea is to have a setup where the Pi wakes up at a given interval, measures the temperature and writes it to a MQTT message queue.
Afterwards the Pi shuts down again.
Internet connectivity is given via a USB dongle.
Using the PiJuice and the solar panel which comes with it, we should be able to take measurements every few hours without being connected to power.

This is a sister project to [balena-weather](https://github.com/hferentschik/balena-weather).

## Balena config

### Device configuration

In order to use the PiJuice real time clock (RTC) and the one wire temperature sensor the following DT overlays and parameters must be set:

DT paramters:

```sh
"spi=on"
```

 DT overlays:

```sh
"i2c-rtc,ds3231,wakeup-source","w1-gpio,gpiopin=22","spi0-cs,cs0_pin=25"
```

*NOTE*: This uses the non default GPIO pin 17 (opposed to 4).

### Device service variables

| Variable        | Service | Description                             | Values                       |
|-----------------|---------|-----------------------------------------|------------------------------|
| API_ENDPOINT    | pijuice | HTTP endpoint to post measurement JSON  | http://lora:8080/api/v1/send |
| START_SSHD      | pijuice | Whether to open SSH port                | [0&vert;1]                   |
| STAY_ALIVE      | pijuice | Whether to stay alive after measurement | [0&vert;1]                   |
| APPKEY          | lora    | TTN appkey                              |                              |
| APPUI           | lora    | TTN appui                               |                              |
| DEVUI           | lora    | TTN devui                               |                              |

## TTN config

### Default uplink payload formatter

```javascript
function decodeUplink(input) {
  tmp = String.fromCharCode(...input.bytes)
  payload = JSON.parse(tmp)
  return {
    data: payload,
    warnings: [],
    errors: []
  };
}
```

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
