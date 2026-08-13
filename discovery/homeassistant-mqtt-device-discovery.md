# Silla Prism — Home Assistant MQTT Device Discovery

This document describes how to expose a Silla Prism wallbox to Home Assistant using **MQTT device discovery**, based on:

- [Home Assistant MQTT discovery](https://www.home-assistant.io/integrations/mqtt#mqtt-discovery)
- [Prism MQTT 4.0](Prism-MQTT-4.0.md) (`docs/Prism-MQTT-4.0.md`)
- Mode values used by the custom `silla_prism` integration (`sensor.py` / `select.py`)

Prism already publishes and consumes MQTT topics. It does **not** publish Home Assistant discovery messages. A bridge, script, firmware update, or one-shot `mosquitto_pub` must publish the discovery payload below. After that, Home Assistant creates a single device and all entities automatically.

Prism MQTT 4.0 does not implement Home Assistant discovery itself. The discovery topic is consumed only by Home Assistant.

To generate a Home Assistant script that publishes this payload on startup, open [prism-mqtt-discovery-generator.html](prism-mqtt-discovery-generator.html).

---

## 1. How device discovery works

Home Assistant subscribes to:

```text
<discovery_prefix>/+/+/config
<discovery_prefix>/+/+/+/config
```

The default `<discovery_prefix>` is `homeassistant`.

For a multi-entity device, Home Assistant recommends **device discovery** (one message for the whole device) instead of one message per entity.

### Discovery topic

```text
<discovery_prefix>/device/<object_id>/config
```

| Part | Value for Prism | Notes |
| --- | --- | --- |
| `<discovery_prefix>` | `homeassistant` | Changeable in MQTT integration options |
| `device` | literal `device` | Required for device discovery |
| `<object_id>` | `prism_<serial>` | Only `[a-zA-Z0-9_-]`. Example: `prism_A00006` |
| `config` | literal `config` | Discovery config topic |

Example:

```text
homeassistant/device/prism_A00006/config
```

Publish the JSON payload with the **retain** flag set (`-r` with `mosquitto_pub`). Home Assistant then recreates the device after a restart.

To delete the device, publish an **empty retained** payload to the same topic.

### Required root keys

Device discovery payloads must include:

| Key | Abbreviation | Meaning |
| --- | --- | --- |
| `device` | `dev` | Device registry info (`identifiers` and `name` are mandatory) |
| `origin` | `o` | Who published the discovery message |
| `components` | `cmps` | Map of entities. Each entry needs `platform` (`p`) and `unique_id` |

Each component key under `cmps` is the discovery component id. Use a stable id such as `state`, `volt`, `set_mode`.

---

## 2. Placeholders used in this document

Replace these values before publishing.

| Placeholder | Source | Example |
| --- | --- | --- |
| `<base_topic>` | Prism app MQTT “Topic base”. Always keep the trailing `/` if Prism is configured that way | `home/prism2/` |
| `<serial>` | Serial from Prism `hello` payload (`Prism-A00006 …`) | `A00006` |
| `<object_id>` | `prism_<serial>` | `prism_A00006` |
| `<port>` | Charge port. `1` for single-cable Prism; `1` left / `2` right on DUO | `1` |
| `<sw>` | Firmware string from `hello` | `3.2.77` |
| `<max_current>` | Rated max current of the wallbox (A) | `16` or `32` |

Prism state topics are `<base_topic>` plus the relative path from the MQTT 4.0 manual. Example with `home/prism2/` and port `1`:

```text
home/prism2/1/state
home/prism2/energy_data/power_grid
home/prism2/hello
```

---

## 3. When to publish discovery

Home Assistant publishes a birth message on `homeassistant/status` with payload `online` when the MQTT integration starts.

Recommended:

1. Subscribe to `homeassistant/status`.
2. When the payload is `online`, publish the discovery config (optionally after a short random delay).
3. Let Prism continue publishing its normal state topics. If those messages are retained, entities get an immediate state.

Alternative: publish the discovery payload once with `retain=true`. That is enough for most setups.

Do **not** retain Prism *state* topics if you also use `expire_after`. Prism only publishes on change; a retained stale value would look fresh after a Home Assistant restart.

Prism has no documented Last Will / availability topic. This payload therefore does not set `availability_topic`. Entities stay available until Home Assistant is restarted without a new discovery message, or until you add your own availability publisher.

---

## 4. Topic and payload map

All relative topics below are appended to `<base_topic>`. Payloads are those defined in Prism MQTT 4.0.

### 4.1 State topics published by Prism

| Prism topic | Payload | HA platform | Entity name | Notes |
| --- | --- | --- | --- | --- |
| `hello` | `Prism-<serial> <fw> (evsemd v…)` | `sensor` | Firmware | Diagnostic. Example: `Prism-A00006 3.2.77 (evsemd v1.1.1)` |
| `<port>/mode` | integer `1`–`8` (see [port mode](#port-mode-portmode)) | `sensor` (enum) + `select` | Port mode | Select commands `1`–`4` |
| `<port>/state` | `1` idle, `2` waiting, `3` charging, `4` pause | `sensor` (enum) | Charge state | |
| `<port>/volt` | float volts | `sensor` | Voltage | Unit `V`, device class `voltage` |
| `<port>/w` | float watts | `sensor` | Output power | Unit `W`, device class `power` |
| `<port>/amp` | integer milliamperes | `sensor` | Output current | Unit `mA`, device class `current` |
| `<port>/pilot` | integer amperes | `sensor` + `number` | Pilot current / current limit | Number writes `set_current_limit` |
| `<port>/user_amp` | integer amperes | `sensor` + `number` | User current | Number writes `set_current_user` |
| `<port>/session_time` | integer seconds | `sensor` | Session time | Device class `duration` |
| `<port>/wh` | float watt-hours | `sensor` | Session energy | `state_class: total` |
| `<port>/wh_total` | float watt-hours | `sensor` | Total energy | `state_class: total_increasing` |
| `<port>/error` | `0` = no error, otherwise error code | `binary_sensor` + `sensor` | Problem / error code | Binary ON when `!= 0` |
| `<port>/input/touch` | press durations, comma-separated | `binary_sensor` × 3 | Touch single / double / long | Sequences `1`, `1,1`, `3` |
| `energy_data/power_grid` | signed watts | `sensor` | Grid power | Positive = import, negative = export |

### 4.2 Command topics consumed by Prism

Home Assistant publishes these when the user changes a number/select or presses a button.

| Prism topic | Payload | HA platform | Entity name |
| --- | --- | --- | --- |
| `<port>/command/set_mode` | `1` solar, `2` normal, `3` paused, `4` hybrid | `select` | Set mode |
| `<port>/command/set_current_user` | integer amperes, no decimals | `number` | Set user current |
| `<port>/command/set_current_limit` | amperes, one decimal allowed (`9.2`) | `number` | Set current limit |
| `<port>/command/enable_night` | any (Prism ignores content) | `button` | Enable schedule |
| `<port>/command/disable_night` | any | `button` | Disable schedule |
| `<port>/command/set_mode_traps` | `-auth` | `button` | Authorize charge |
| `<port>/command/set_mode_traps` | `+auth` | `button` | Deauthorize charge |

`set_current_user` is the MQTT equivalent of the Prism UI `+` / `-` buttons. Do **not** use it for dynamic load balancing; use `set_current_limit` instead.

Authorize / deauthorize only works when the cable is connected and autostart is disabled.

### 4.3 Command result topics published by Prism

Not required to create the device. Optional diagnostic entities.

| Prism topic | Payload | Suggested HA platform |
| --- | --- | --- |
| `commandresult/<command>/success` | message on success (content undocumented) | `binary_sensor` with `off_delay`, or `event` |
| `commandresult/<command>/error` | error string, e.g. `Bad syntax, mode must be [0-9]` | `sensor` |

`<command>` is the command name: `set_mode`, `set_current_user`, `set_current_limit`, `enable_night`, `disable_night`, `set_mode_traps`.

### 4.4 Powerwall-only topics

Present only when Powerwall communication is enabled in the Silla app.

| Prism topic | Payload | HA platform | Entity name |
| --- | --- | --- | --- |
| `energy_data/power_solar` | watts | `sensor` | Solar power |
| `energy_data/power_house` | watts | `sensor` | House power |

The MQTT 4.0 PDF examples for these two topics incorrectly show `<base_topic>/1/power_solar`. The topic names in the index are `energy_data/power_solar` and `energy_data/power_house`. Use the `energy_data/…` paths, matching `energy_data/power_grid`.

---

## 5. Payload encodings Home Assistant must apply

Prism publishes raw numbers. Device discovery must convert them with templates.

### Charge state (`<port>/state`)

| Prism payload | Home Assistant state |
| --- | --- |
| `1` | `idle` |
| `2` | `waiting` |
| `3` | `charging` |
| `4` | `pause` |

```jinja
{% set map = {'1':'idle','2':'waiting','3':'charging','4':'pause'} %}{{ map.get(value, 'unknown') }}
```

### Port mode (`<port>/mode`)

Prism MQTT 4.0 documents payloads `1`, `2`, `3`, and `7`. The custom `silla_prism` integration also maps `4`, `5`, `6`, and `8` (observed on firmware that the 4.0 manual does not cover). Use the full custom-integration table for discovery so Home Assistant never shows a raw number.

The integration stores the **option key** as entity state. Friendly names come from translations.

| Prism payload | Option key | Friendly name | MQTT 4.0 | Custom integration | Select |
| --- | --- | --- | --- | --- | --- |
| `1` | `solar` | OnlySun | Solar | yes | commandable |
| `2` | `normal` | Boost | Normal | yes | commandable |
| `3` | `paused` | Paused | Pausa | yes | commandable |
| `4` | `hybrid` | Hybrid | not documented | yes | commandable |
| `5` | `suspended` | Suspended | not documented | yes (reported only) | — |
| `6` | `unknown` | Unknown | not documented | yes (reported only) | — |
| `7` | `unknown` | Unknown | Charge interrupted by load balancing | yes (reported only) | shown as `paused` |
| `8` | `autolimit` | Auto limit | not documented | yes (reported only) | — |

The select entity only offers the four commandable modes: `solar`, `normal`, `paused`, `hybrid`. When Prism reports `7`, the custom integration remaps that value to `paused` on the select (load-balance interrupt is not a mode you can set). The mode **sensor** still shows `unknown` for payload `7`, matching `sensor.py`.

Sensor template (same index order as `current_port_mode` in the custom integration):

```jinja
{% set map = {'1':'solar','2':'normal','3':'paused','4':'hybrid','5':'suspended','6':'unknown','7':'unknown','8':'autolimit'} %}{{ map.get(value, 'unknown') }}
```

Select value template:

```jinja
{% set map = {'1':'solar','2':'normal','3':'paused','4':'hybrid','7':'paused'} %}{{ map.get(value, 'normal') }}
```

Select command template (Home Assistant → Prism):

```jinja
{{ {'solar':1,'normal':2,'paused':3,'hybrid':4}[value] }}
```

### Error (`<port>/error`)

| Prism payload | Binary sensor |
| --- | --- |
| `0` | `OFF` |
| any other integer | `ON` |

```jinja
{{ 'ON' if value | int != 0 else 'OFF' }}
```

Keep a separate numeric sensor on the same topic so the error code remains visible.

### Touch (`<port>/input/touch`)

| Sequence | Gesture | `off_delay` |
| --- | --- | --- |
| `1` | single short press | 1 s |
| `1,1` | double short press | 1 s |
| `3` | 3 s long press | 1 s |

A sequence ends after 0.8 s idle or after more than 30 presses. Other sequences (`1,1,3`, …) can be added the same way.

### Current limit number

- `set_current_user`: integer, `step: 1`, `min: 6`, `max: <max_current>`
- `set_current_limit`: one decimal, `step: 0.1`, `min: 6`, `max: <max_current>`
- `set_current_limit` command template should pass the number through (`{{ value }}`)
- `set_current_user` should send an integer (`{{ value | int }}`)

### Night schedule and auth buttons

| Button | `command_topic` | `payload_press` |
| --- | --- | --- |
| Enable night schedule | `<port>/command/enable_night` | `1` |
| Disable night schedule | `<port>/command/disable_night` | `1` |
| Authorize | `<port>/command/set_mode_traps` | `-auth` |
| Deauthorize | `<port>/command/set_mode_traps` | `+auth` |

Schedule times must already be configured in the Silla app.

---

## 6. Device discovery payload (single-port Prism)

**Topic** (retain = true):

```text
homeassistant/device/prism_A00006/config
```

Replace `A00006`, `home/prism2/`, firmware, and max current as needed.

```json
{
  "dev": {
    "ids": ["prism_A00006"],
    "name": "Silla Prism",
    "mf": "Silla",
    "mdl": "Prism",
    "sw": "3.2.77",
    "sn": "A00006"
  },
  "o": {
    "name": "silla-prism-mqtt-discovery",
    "sw": "4.0",
    "url": "https://silla.industries/centro-assistenza/"
  },
  "cmps": {
    "hello": {
      "p": "sensor",
      "name": "Firmware",
      "unique_id": "prism_A00006_hello",
      "stat_t": "home/prism2/hello",
      "ent_cat": "diagnostic",
      "icon": "mdi:information-outline"
    },
    "state": {
      "p": "sensor",
      "name": "Charge state",
      "unique_id": "prism_A00006_state",
      "stat_t": "home/prism2/1/state",
      "dev_cla": "enum",
      "ops": ["idle", "waiting", "charging", "pause", "unknown"],
      "val_tpl": "{% set map = {'1':'idle','2':'waiting','3':'charging','4':'pause'} %}{{ map.get(value, 'unknown') }}",
      "ic": "mdi:ev-station"
    },
    "mode": {
      "p": "sensor",
      "name": "Port mode",
      "unique_id": "prism_A00006_mode",
      "stat_t": "home/prism2/1/mode",
      "dev_cla": "enum",
      "ops": ["solar", "normal", "paused", "hybrid", "suspended", "unknown", "autolimit"],
      "val_tpl": "{% set map = {'1':'solar','2':'normal','3':'paused','4':'hybrid','5':'suspended','6':'unknown','7':'unknown','8':'autolimit'} %}{{ map.get(value, 'unknown') }}",
      "ic": "mdi:solar-power"
    },
    "volt": {
      "p": "sensor",
      "name": "Voltage",
      "unique_id": "prism_A00006_volt",
      "stat_t": "home/prism2/1/volt",
      "dev_cla": "voltage",
      "stat_cla": "measurement",
      "unit_of_meas": "V",
      "sug_dsp_prc": 0
    },
    "w": {
      "p": "sensor",
      "name": "Output power",
      "unique_id": "prism_A00006_w",
      "stat_t": "home/prism2/1/w",
      "dev_cla": "power",
      "stat_cla": "measurement",
      "unit_of_meas": "W",
      "sug_dsp_prc": 0
    },
    "amp": {
      "p": "sensor",
      "name": "Output current",
      "unique_id": "prism_A00006_amp",
      "stat_t": "home/prism2/1/amp",
      "dev_cla": "current",
      "stat_cla": "measurement",
      "unit_of_meas": "mA",
      "sug_dsp_prc": 0
    },
    "pilot": {
      "p": "sensor",
      "name": "Pilot current",
      "unique_id": "prism_A00006_pilot",
      "stat_t": "home/prism2/1/pilot",
      "dev_cla": "current",
      "stat_cla": "measurement",
      "unit_of_meas": "A",
      "sug_dsp_prc": 0
    },
    "user_amp": {
      "p": "sensor",
      "name": "User current",
      "unique_id": "prism_A00006_user_amp",
      "stat_t": "home/prism2/1/user_amp",
      "dev_cla": "current",
      "stat_cla": "measurement",
      "unit_of_meas": "A",
      "sug_dsp_prc": 0
    },
    "session_time": {
      "p": "sensor",
      "name": "Session time",
      "unique_id": "prism_A00006_session_time",
      "stat_t": "home/prism2/1/session_time",
      "dev_cla": "duration",
      "stat_cla": "measurement",
      "unit_of_meas": "s",
      "sug_dsp_prc": 0
    },
    "wh": {
      "p": "sensor",
      "name": "Session energy",
      "unique_id": "prism_A00006_wh",
      "stat_t": "home/prism2/1/wh",
      "dev_cla": "energy",
      "stat_cla": "total",
      "unit_of_meas": "Wh",
      "sug_dsp_prc": 0
    },
    "wh_total": {
      "p": "sensor",
      "name": "Total energy",
      "unique_id": "prism_A00006_wh_total",
      "stat_t": "home/prism2/1/wh_total",
      "dev_cla": "energy",
      "stat_cla": "total_increasing",
      "unit_of_meas": "Wh",
      "sug_dsp_prc": 0
    },
    "error_code": {
      "p": "sensor",
      "name": "Error code",
      "unique_id": "prism_A00006_error_code",
      "stat_t": "home/prism2/1/error",
      "ent_cat": "diagnostic",
      "ic": "mdi:alert-circle-outline"
    },
    "power_grid": {
      "p": "sensor",
      "name": "Grid power",
      "unique_id": "prism_A00006_power_grid",
      "stat_t": "home/prism2/energy_data/power_grid",
      "dev_cla": "power",
      "stat_cla": "measurement",
      "unit_of_meas": "W",
      "sug_dsp_prc": 0
    },
    "error": {
      "p": "binary_sensor",
      "name": "Problem",
      "unique_id": "prism_A00006_error",
      "stat_t": "home/prism2/1/error",
      "dev_cla": "problem",
      "val_tpl": "{{ 'ON' if value | int != 0 else 'OFF' }}",
      "pl_on": "ON",
      "pl_off": "OFF"
    },
    "touch_single": {
      "p": "binary_sensor",
      "name": "Touch single",
      "unique_id": "prism_A00006_touch_single",
      "stat_t": "home/prism2/1/input/touch",
      "ent_cat": "diagnostic",
      "dev_cla": "occupancy",
      "val_tpl": "{{ 'ON' if value == '1' else 'OFF' }}",
      "pl_on": "ON",
      "pl_off": "OFF",
      "off_dly": 1
    },
    "touch_double": {
      "p": "binary_sensor",
      "name": "Touch double",
      "unique_id": "prism_A00006_touch_double",
      "stat_t": "home/prism2/1/input/touch",
      "ent_cat": "diagnostic",
      "dev_cla": "occupancy",
      "val_tpl": "{{ 'ON' if value == '1,1' else 'OFF' }}",
      "pl_on": "ON",
      "pl_off": "OFF",
      "off_dly": 1
    },
    "touch_long": {
      "p": "binary_sensor",
      "name": "Touch long",
      "unique_id": "prism_A00006_touch_long",
      "stat_t": "home/prism2/1/input/touch",
      "ent_cat": "diagnostic",
      "dev_cla": "occupancy",
      "val_tpl": "{{ 'ON' if value == '3' else 'OFF' }}",
      "pl_on": "ON",
      "pl_off": "OFF",
      "off_dly": 1
    },
    "set_mode": {
      "p": "select",
      "name": "Set mode",
      "unique_id": "prism_A00006_set_mode",
      "ent_cat": "config",
      "stat_t": "home/prism2/1/mode",
      "cmd_t": "home/prism2/1/command/set_mode",
      "ops": ["solar", "normal", "paused", "hybrid"],
      "val_tpl": "{% set map = {'1':'solar','2':'normal','3':'paused','4':'hybrid','7':'paused'} %}{{ map.get(value, 'normal') }}",
      "cmd_tpl": "{{ {'solar':1,'normal':2,'paused':3,'hybrid':4}[value] }}"
    },
    "set_current_user": {
      "p": "number",
      "name": "Set user current",
      "unique_id": "prism_A00006_set_current_user",
      "ent_cat": "config",
      "dev_cla": "current",
      "unit_of_meas": "A",
      "min": 6,
      "max": 16,
      "step": 1,
      "mode": "box",
      "stat_t": "home/prism2/1/user_amp",
      "cmd_t": "home/prism2/1/command/set_current_user",
      "cmd_tpl": "{{ value | int }}"
    },
    "set_current_limit": {
      "p": "number",
      "name": "Set current limit",
      "unique_id": "prism_A00006_set_current_limit",
      "ent_cat": "config",
      "dev_cla": "current",
      "unit_of_meas": "A",
      "min": 6,
      "max": 16,
      "step": 0.1,
      "mode": "box",
      "stat_t": "home/prism2/1/pilot",
      "cmd_t": "home/prism2/1/command/set_current_limit",
      "cmd_tpl": "{{ value }}"
    },
    "enable_night": {
      "p": "button",
      "name": "Enable schedule",
      "unique_id": "prism_A00006_enable_night",
      "ent_cat": "config",
      "cmd_t": "home/prism2/1/command/enable_night",
      "pl_prs": "1",
      "ic": "mdi:weather-night"
    },
    "disable_night": {
      "p": "button",
      "name": "Disable schedule",
      "unique_id": "prism_A00006_disable_night",
      "ent_cat": "config",
      "cmd_t": "home/prism2/1/command/disable_night",
      "pl_prs": "1",
      "ic": "mdi:weather-night-off"
    },
    "auth": {
      "p": "button",
      "name": "Authorize",
      "unique_id": "prism_A00006_auth",
      "cmd_t": "home/prism2/1/command/set_mode_traps",
      "pl_prs": "-auth",
      "ic": "mdi:lock-open-variant"
    },
    "deauth": {
      "p": "button",
      "name": "Deauthorize",
      "unique_id": "prism_A00006_deauth",
      "cmd_t": "home/prism2/1/command/set_mode_traps",
      "pl_prs": "+auth",
      "ic": "mdi:lock"
    }
  }
}
```

Topics are written in full. Device discovery does **not** allow a root-level `~` base-topic key (`extra keys not allowed @ data['~']`). The `~` shortcut only works in single-component discovery, or as a key inside an individual component object.

Abbreviations used (`dev`, `o`, `cmps`, `p`, `stat_t`, `cmd_t`, …) are the official MQTT discovery abbreviations.

---

## 7. Optional Powerwall components

Add these keys inside `cmps` only if Powerwall MQTT topics are enabled:

```json
"power_solar": {
  "p": "sensor",
  "name": "Solar power",
  "unique_id": "prism_A00006_power_solar",
  "stat_t": "home/prism2/energy_data/power_solar",
  "dev_cla": "power",
  "stat_cla": "measurement",
  "unit_of_meas": "W",
  "sug_dsp_prc": 0
},
"power_house": {
  "p": "sensor",
  "name": "House power",
  "unique_id": "prism_A00006_power_house",
  "stat_t": "home/prism2/energy_data/power_house",
  "dev_cla": "power",
  "stat_cla": "measurement",
  "unit_of_meas": "W",
  "sug_dsp_prc": 0
}
```

---

## 8. Prism DUO (two ports)

Keep one discovery message and one device. Duplicate every port-scoped component, change:

- component id: `state` → `state_2`
- `unique_id`: `prism_A00006_state` → `prism_A00006_p2_state`
- `name`: prefix with `Port 2`
- topics: `home/prism2/1/…` → `home/prism2/2/…`

Shared (not port-scoped) components stay unique:

- `hello`
- `energy_data/power_grid`
- `energy_data/power_solar`
- `energy_data/power_house`

Example for port 2 charge state:

```json
"state_2": {
  "p": "sensor",
  "name": "Port 2 charge state",
  "unique_id": "prism_A00006_p2_state",
  "stat_t": "home/prism2/2/state",
  "dev_cla": "enum",
  "ops": ["idle", "waiting", "charging", "pause", "unknown"],
  "val_tpl": "{% set map = {'1':'idle','2':'waiting','3':'charging','4':'pause'} %}{{ map.get(value, 'unknown') }}",
  "ic": "mdi:ev-station"
}
```

Port-scoped components to duplicate: `state`, `mode`, `volt`, `w`, `amp`, `pilot`, `user_amp`, `session_time`, `wh`, `wh_total`, `error_code`, `error`, `touch_single`, `touch_double`, `touch_long`, `set_mode`, `set_current_user`, `set_current_limit`, `enable_night`, `disable_night`, `auth`, `deauth`.

---

## 9. Optional command-result components

```json
"cmd_error": {
  "p": "sensor",
  "name": "Last command error",
  "unique_id": "prism_A00006_cmd_error",
  "stat_t": "home/prism2/commandresult/+/error",
  "ent_cat": "diagnostic",
  "ic": "mdi:alert"
}
```

Home Assistant MQTT sensors do not subscribe to wildcards in `state_topic`. Publish one sensor per command instead, for example `home/prism2/commandresult/set_mode/error`, or handle results outside discovery.

---

## 10. Publish / remove examples

Set broker host, credentials, serial, and base topic first.

### Discover the device

```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -r \
  -t "homeassistant/device/prism_A00006/config" \
  -f prism-discovery.json
```

`prism-discovery.json` is the JSON from section 6.

### Remove the device

```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -r \
  -t "homeassistant/device/prism_A00006/config" \
  -m ""
```

### Remove one component without deleting the device

Re-publish the full device payload, but replace that component with only the platform key:

```json
"touch_long": {
  "p": "binary_sensor"
}
```

Then publish again with that component omitted so Home Assistant stores the cleaned config.

---

## 11. Entity checklist (single-port, no Powerwall)

| Component id | Platform | Prism state topic | Prism command topic | Command payload |
| --- | --- | --- | --- | --- |
| `hello` | sensor | `hello` | — | — |
| `state` | sensor | `1/state` | — | `1`–`4` |
| `mode` | sensor | `1/mode` | — | `1`–`8` (see [port mode](#port-mode-portmode)) |
| `volt` | sensor | `1/volt` | — | volts |
| `w` | sensor | `1/w` | — | watts |
| `amp` | sensor | `1/amp` | — | mA |
| `pilot` | sensor | `1/pilot` | — | A |
| `user_amp` | sensor | `1/user_amp` | — | A |
| `session_time` | sensor | `1/session_time` | — | seconds |
| `wh` | sensor | `1/wh` | — | Wh |
| `wh_total` | sensor | `1/wh_total` | — | Wh |
| `error_code` | sensor | `1/error` | — | integer |
| `power_grid` | sensor | `energy_data/power_grid` | — | signed W |
| `error` | binary_sensor | `1/error` | — | `0` / other |
| `touch_single` | binary_sensor | `1/input/touch` | — | `1` |
| `touch_double` | binary_sensor | `1/input/touch` | — | `1,1` |
| `touch_long` | binary_sensor | `1/input/touch` | — | `3` |
| `set_mode` | select | `1/mode` | `1/command/set_mode` | `1`,`2`,`3`,`4` |
| `set_current_user` | number | `1/user_amp` | `1/command/set_current_user` | integer A |
| `set_current_limit` | number | `1/pilot` | `1/command/set_current_limit` | A with 1 decimal |
| `enable_night` | button | — | `1/command/enable_night` | `1` |
| `disable_night` | button | — | `1/command/disable_night` | `1` |
| `auth` | button | — | `1/command/set_mode_traps` | `-auth` |
| `deauth` | button | — | `1/command/set_mode_traps` | `+auth` |

That is the complete set of discovery topics and payloads needed to activate the Prism as a Home Assistant MQTT device.

---

## 12. Relation to the custom `silla_prism` integration

This discovery approach uses the built-in MQTT integration. It does **not** require the custom component in this repository.

Differences worth knowing:

- Port mode uses the custom integration mapping (`1`–`8`, including `hybrid` / `suspended` / `autolimit`), not only the four values in the MQTT 4.0 manual.
- The custom integration derives a virtual grid-energy integral in Home Assistant. MQTT discovery cannot compute that; use a [Riemann sum helper](https://www.home-assistant.io/integrations/integration/) on `Grid power` if needed.
- The custom integration infers “online” from `1/volt` with an expiry timer. Discovery above does not, because Prism has no availability topic.

Use either MQTT discovery **or** the custom integration, not both against the same unique ids, or you will get duplicate devices.
