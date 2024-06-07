#  # Silla Prism Solar custom integration

**Warning**: This repository is in a early stage. And is not yet stable.

![Silla Prism Solar](image.png)

This repository contains a custom integration to integrate a Silla Prism Wallbox inside HomeAssistant

## Installation

Prerequisites: A working MQTT server.

1) Configure the Prism Wallbox to work with your MQTT server  [has shown in manual](https://support.silla.industries/wp-content/uploads/2023/09/DOC-Prism_MQTT_Manual-rel.2.0_rev.-20220105-EN.pdf).
2) Configure and enable the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) for HomeAssistant
3) Install the custom integration from this repository [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Stefano+Pagnottelli&repository=https%3A%2F%2Fgithub.com%2Fpersuader72%2Fcustom-components.git&category=integration)

## Usage

1. Add integration Silla Prism using the dashboard  [![Open your Home Assistant instance and start setting up a new integration of a specific brand.](https://my.home-assistant.io/badges/brand.svg)](https://my.home-assistant.io/redirect/brand/?brand=silla_prism) 

2. Keep note of base path for all Prism topics

   ![Prism manual](images/setup3.png)

3. When asked for connection settings set the the base path for all Prism topics. For now it is important to leave a / at the end of the topics as shown in the following picture)
   ![Configure Silla Prism](images/setup2.png)

   

## Entities

| Topic                       | Desription                                                   | Entity      | Unit                                   |
| --------------------------- | ------------------------------------------------------------ | ----------- | -------------------------------------- |
| ?/1/state                   | Current state of Prism                                       | Sensor      | "idle", "waiting", "charging", "pause" |
| ?/1/volt                    | Measured voltage from grid                                   | Sensor      | V                                      |
| ?/1/w                       | Power provided to the charging port                          | Sensor      | W                                      |
| ?/1/amp                     | Current provided to the charging port                        | Sensor      | mA                                     |
| ?/1/pilot                   | Current driven by the car                                    | Sensor      | A                                      |
| ?/1/user_amp                | Current limit set by user                                    | Sensor      | A                                      |
| ?/1/session_time            | Duration of the current session                              | Sensor      | s                                      |
| ?/1/wh                      | Energy provided to the charging port during the current session | Sensor      | Wh                                     |
| ?/1/wh_total                | Total energy                                                 | Sensor      | Wh                                     |
| ?/1/error                   | Error code                                                   | (TODO)      |                                        |
| ?/1/mode                    | Current port mode                                            | Sensor      |                                        |
| ?/1/input/touch             | Touch button sequence events                                 | BinarySenor | single,double,long events              |
| ?/energy_data/power_grid    | Input power from grid                                        | Sensor      | W                                      |
| ?/command/set_mode          | Set the working mode                                         | Select      | Solar,Normal,Paused                    |
| ?/command/set_current_user  | Set the user current limit                                   | Number      | A                                      |
| ?/command/set_current_limit | Set the  current limit                                       | Number      | A                                      |

## Frontend configuration

![Charger](images/setup4.png)

It's possible to configure the [EV Charger Card](https://github.com/tmjo/charger-card) using the configuration example [provided](https://github.com/persuader72/custom-components/blob/main/charger-card.yaml) in this repository 

# Touch button and Automations

This are some example automations for the touch button events

### Start charge after single touch event if the wallbox is in pause state

```yaml
alias: Avvia ricarica dopo pressione pulsante
description: Avvia ricarica dopo pressione pulsante
trigger:
  - platform: state
    entity_id:
      - binary_sensor.silla_prism_input_touch
    from: "off"
    to: "on"
condition:
  - condition: state
    entity_id: sensor.prism_stato_wallbox
    state: pause
action:
  - service: mqtt.publish
    data:
      qos: "0"
      retain: true
      topic: prism/1/command/set_mode
      payload: "2"
mode: single
```

### Stop charge after single touch event if the wallbox is in charging state

```yaml
alias: Interrompi ricarica dopo pressione pulsante
description: Interrompi ricarica dopo pressione pulsante
trigger:
  - platform: state
    entity_id:
      - binary_sensor.silla_prism_input_touch
    from: "off"
    to: "on"
condition:
  - condition: state
    entity_id: sensor.prism_stato_wallbox
    state: charging
action:
  - service: mqtt.publish
    metadata: {}
    data:
      qos: "0"
      retain: true
      topic: prism/1/command/set_mode
      payload: "3"
mode: single
```



## TODO

1. Translations (English)
2. Expire non sensor entities
3. Mixed Italian and English in code and documentation.
4. Resolve TODOs in code
5. Handle input touch button
