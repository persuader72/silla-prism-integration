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

| Topic                       | Desription                                                   | Entity | Unit                                   |
| --------------------------- | ------------------------------------------------------------ | ------ | -------------------------------------- |
| ?/1/state                   | Stato attuale della Prism                                    | Sensor | "idle", "waiting", "charging", "pause" |
| ?/1/volt                    | Tensione attualmente misurata da Prism                       | Sensor | V                                      |
| ?/1/w                       | Potenza attualmente erogata dalla porta di ricarica          | Sensor | W                                      |
| ?/1/amp                     | Corrente attualmente erogata dalla porta di ricarica         | Sensor | mA                                     |
| ?/1/pilot                   | Corrente pilotata all’auto                                   | Sensor | A                                      |
| ?/1/user_amp                | Corrente impostata dall’utente                               | Sensor | A                                      |
| ?/1/session_time            | Durata della sessione di ricarica attuale                    | Sensor | s                                      |
| ?/1/wh                      | Energia erogata dalla porta di ricarica durante la sessione in corso | Sensor | Wh                                     |
| ?/1/wh_total                | Energia totale erogata da Prism                              | Sensor | Wh                                     |
| ?/1/error                   | Codice di errore relativo alla porta                         | (TODO) |                                        |
| ?/1/mode                    | Modalità attuale della porta                                 | Sensor |                                        |
| ?/1/input/touch             | Sequenza pulsante touch                                      | (TODO) |                                        |
| ?/energy_data/power_grid    | Potenza attualmente prelevata dalla rete                     | Sensor | W                                      |
| ?/command/set_mode          | Imposta la modalità di Prism                                 | Select |                                        |
| ?/command/set_current_user  | Imposta la corrente massima di ricarica specificata dall’utente | Number | A                                      |
| ?/command/set_current_limit | Imposta il limite di corrente di ricarica, in ampere         | Number | A                                      |
|                             |                                                              |        |                                        |

## TODO

1. Translations (English)
2. Expire non sensor entities
3. Mixed Italian and English in code and documentation.
4. Resolve TODOs in code
