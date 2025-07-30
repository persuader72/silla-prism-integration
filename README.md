#  # Silla Prism Solar custom integration

![Silla Prism Solar](image.png)

This repository contains a custom integration to integrate a Silla Prism EVSE inside HomeAssistant

## Installation

Prerequisites: A working MQTT server.

1) Configure the Prism EVSE to work with your MQTT server  [has shown in manual](https://support.silla.industries/wp-content/uploads/2023/09/DOC-Prism_MQTT_Manual-rel.2.0_rev.-20220105-EN.pdf).
2) Configure and enable the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) for HomeAssistant
3) Install the custom integration from this repository [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=https%3A%2F%2Fgithub.com%2Fpersuader72%2Fsilla-prism-integration&owner=Stefano+Pagnottelli)

## Usage

1. Add integration Silla Prism using the dashboard  [![Open your Home Assistant instance and start setting up a new integration of a specific brand.](https://my.home-assistant.io/badges/brand.svg)](https://my.home-assistant.io/redirect/brand/?brand=silla_prism) 

2. Keep note of base path for all Prism topics

   ![Prism manual](images/setup3.png)

3. **Topic** Set the the base path for all Prism topics must be the same set in the Prism configuration page seen before. For now it is important to leave a **/** at the end of the topic as shown in the picture below)

4. **number of ports ** If you have more the one port (like Prism Duo) on your device set here the corresponding number of ports otherwise if you have only one port you can leave this field at the default value of 1

5. **serial number** or **unique code** if you have more then one Prism connected to HomeAssistant you have to fill this value with a unique code (you can use the serial number) otherwise if you have only one Prism you can leave this field blank.

6. **Enable virtual sensor** this enable additional sensors derived from the original Prism sensors, like the counter of the total energy consumed from the power grid. 

7. ![Configure Silla Prism](images/setup2.png)

## Solar automations

Solar automation is a work in progress. And we be described in [Solar](solar.md) page 

## Entities

| Entity ID                         | Type         | Description                                                  | Unit                                   |
| --------------------------------- | ------------ | ------------------------------------------------------------ | -------------------------------------- |
| silla_prism_online                | BinarySensor | Sensor to find if Prism is connected or not                  |                                        |
| silla_prism_current_state         | Sensor       | Current state of Prism                                       | "idle", "waiting", "charging", "pause" |
| silla_prism_power_grid_voltage    | Sensor       | Measured voltage from grid                                   | V                                      |
| silla_prism_output_power          | Sensor       | Power provided to the charging port                          | W                                      |
| silla_prism_output_current        | Sensor       | Current provided to the charging port                        | mA                                     |
| silla_prism_output_car_current    | Sensor       | Current driven by the car                                    | A                                      |
| silla_prism_current_set_by_user   | Sensor       | Current limit set by user                                    | A                                      |
| silla_prism_session_time          | Sensor       | Duration of the current session                              | s                                      |
| silla_prism_session_output_energy | Sensor       | Energy provided to the charging port during the current session | Wh                                     |
| silla_prism_total_output_energy   | Sensor       | Total energy                                                 | Wh                                     |
| ?/1/error                         | (TODO)       | Error code                                                   |                                        |
| silla_prism_current_port_mode     | Sensor       | Current port mode                                            | solar,normal,paused                    |
| silla_prism_input_grid_power      | Sensor       | Input power from grid                                        | W                                      |
| silla_prism_set_max_current       | Number       | Set the user current limit                                   | A                                      |
| silla_prism_set_current_limit     | Number       | Set the  current limit                                       | A                                      |
| silla_prism_set_mode              | Select       | Set current port mode                                        | solar,normal,paused                    |
| silla_prism_touch_sigle           | BinarySensor | Goes on for 1 second after a single touch gesture            | On,Off                                 |
| silla_prism_touch_double          | BinarySensor | Goes on for 1 second after a double touch gesture            | On,Off                                 |
| silla_prism_touch_long            | BinarySensor | Goes on for 1 second after a long touch gesture              | On,Off                                 |

## Computed Entities

Computed entities are not directly measured from Prism but are derived from other measurements. 

| Entity ID                     | Type   | Description                  | Unit |
| ----------------------------- | ------ | ---------------------------- | ---- |
| silla_prism_input_grid_energy | Sensor | Total energy taken from grid | Wh   |
|                               |        |                              |      |
|                               |        |                              |      |


# Setting up the user interface

## With the charger card integration

![Charger](images/setup4.png)

It's possible to configure the [EV Charger Card](https://github.com/tmjo/charger-card) using the configuration example [provided](https://github.com/persuader72/custom-components/blob/main/charger-card/template.yaml) in this repository 

## With automations and helpers

The following four examples show how to set up a simple interface
via Home Assistant helpers (input booleans) and automations.  You do
not have to use all four!

These automations and input booleans can also be used with the
EV Charger Card, though they are most useful without it.

### Start/stop charge with a switch

For now, disable Autostart on the Prism (later I will show how to keep
it enabled).

Create an "Input Boolean" called `prism_charge` (suggested icon:
`mdi:ev-plug-type2`).  The following automation starts and stop the
charging process when `prism_charge` is toggled:

```yaml
alias: Prism - authorize/deauthorize
triggers:
  - trigger: state
    entity_id:
      - input_boolean.prism_charge
actions:
  - if:
      - condition: state
        entity_id: sensor.silla_prism_current_state
        state: idle
    then:
      - action: input_boolean.turn_off
        target:
          entity_id: input_boolean.prism_charge
      - stop: No charging cable connected
  - if:
      - condition: state
        entity_id: sensor.silla_prism_current_state
        state: pause
    then:
      - action: button.press
        target:
          entity_id: button.silla_prism_set_mode_traps_auth
    else:
      - action: button.press
        target:
          entity_id: button.silla_prism_set_mode_traps_noauth
mode: single
```

### Start/stop charge with a single touch on the Prism

With the previous set up, Autostart is disabled, but starting/stopping
the charge process with the Prism key fobs does not synchronize with
the Input Boolean.

Instead of using the key fobs, you can configure another automation that
toggles the Input Boolean with a single touch on the Prism's sensor:

```yaml
alias: Prism - toggle charge after single touch event
description: ""
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.silla_prism_touch_sigle
    to: on
actions:
  - action: input_boolean.toggle
    target:
      entity_id: input_boolean.prism_charge
mode: single
```

### Same setup but with Autostart enabled

If you prefer to keep Autostart enabled or to use the key fobs, just ensure
`prism_charge` changes to on and off when `sensor.silla_prism_current_state`
becomes respectively `charging` or anything else:

```yaml
alias: Prism - synchronize charging state
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.silla_prism_current_state
    id: changed_prism
actions:
  - if:
      - condition: state
        entity_id: sensor.silla_prism_current_state
        state: charging
    then:
      - action: input_boolean.turn_on
        target:
          entity_id: input_boolean.prism_charge
  - else:
      - action: input_boolean.turn_off
        target:
          entity_id: input_boolean.prism_charge
mode: single
```

This can be used with any combination of the previous automations.

### Switch normal/solar modes from Home Assistant

Create an "Input Boolean" called `prism_solar_mode` (suggested icon:
`mdi:weather-sunny`).  The following automation keeps it synchronized
with the "solar" and "normal" modes of the Prism dashboard:

```yaml
alias: Prism - synchronize solar/normal mode
description: ""
triggers:
  - trigger: state
    entity_id:
      - input_boolean.prism_solar_mode
    id: changed_helper
  - trigger: state
    entity_id:
      - sensor.silla_prism_current_port_mode
    id: changed_prism
actions:
  - if:
      - condition: trigger
        id:
          - changed_helper
    then:
      - if:
          - condition: state
            entity_id: input_boolean.prism_solar_mode
            state: on
        then:
          - action: select.select_option
            data:
              option: solar
            target:
              entity_id: select.silla_prism_set_mode
        else:
          - action: select.select_option
            data:
              option: normal
            target:
              entity_id: select.silla_prism_set_mode
    else:
      - if:
          - condition: state
            entity_id: sensor.silla_prism_current_port_mode
            state: solar
        then:
          - action: input_boolean.turn_on
            target:
              entity_id: input_boolean.prism_solar_mode
      - if:
          - condition: state
            entity_id: sensor.silla_prism_current_port_mode
            state: normal
        then:
          - action: input_boolean.turn_off
            target:
              entity_id: input_boolean.prism_solar_mode
mode: single
```
