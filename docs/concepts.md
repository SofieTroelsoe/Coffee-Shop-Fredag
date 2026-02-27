# Concepts Clarification (Pre-Implementation)

This document rewrites your current idea into clear technical terms before implementation.
It intentionally avoids code and focuses on confirmed requirements, interfaces, and open questions.

## Project Scope (as currently understood)

You want a small simulated city in central Copenhagen where 5 people move continuously within 800 m of the center (lat: 55.676178955076935, lon: 12.568603532313528). A weather cycle alternates between sun and rain (20 seconds sun, 10 seconds rain). During rain, people should move continuously to their nearest coffee shop within a straight line (5 total shops with set locations). It is fine if multiple people choose the same coffee shop. When the rain stops, people move again instantly. A dashboard map should show people and coffee shops, and switch to a darker visual style while raining.
Weather and Observer are separate agents: Weather publishes full weather state, and Observer republishes rain-specific status for control logic.
Runs are non-deterministic (no fixed random seed), but all people spawn at the city center at simulation start.
The architecture uses separate notebooks per agent type, and MQTT is the only communication channel between agents.
The dashboard is visualization-only (read-only): it must not publish control messages.
Coffee shop locations are static configuration data, not a separate runtime agent.
The simulation runs continuously (no fixed end duration).
The dashboard refreshes whenever people positions change and whenever weather state changes.
Each simulation notebook includes a dedicated bottom stop cell so you can stop the running loop manually from one place.

---

## 1) Four Components Rewritten in Technical Language

## Trigger
The trigger is the **state change event** that initiates behavior updates in other agents.

- Primary trigger: weather phase transition (`sun -> rain`, `rain -> sun`)
- Secondary trigger: periodic simulation tick (for movement updates)
- Expected trigger cadence: fixed time-step updates (for every 1 second)
- Weather cycle behavior is deterministic by timing (20s sun, 10s rain)

## Observer
The observer is the **sensing and state-reporting layer**.

- It is a separate agent/process from the Weather agent
- It detects and broadcasts whether it is currently raining
- It provides the latest environmental state to other agents
- It does not decide destination logic; it only reports facts/events

## Control
The control component is the **decision layer** that converts observed state into commands.

- On rain: compute nearest coffee shop per person and issue movement intent
- On sun: resume random-walk behavior intent
- It should be deterministic given the same inputs (person positions + weather state + shop locations)
- During each rain episode, each person selects one nearest coffee shop at rain start and keeps that target until rain ends.

## Response
The response component is the **actuation/execution layer**.

- Person agents apply control commands and update their positions over time
- The visualization reflects updated positions, weather state, and map theme
- Response includes both movement behavior and dashboard rendering updates

---

## 2) MQTT Topic Clarification per Agent

Below is a topic contract proposal based on your outline and workshop conventions.
Assumed base topic from config: `simulated-city`.

### Agent: Weather
- Publishes:
  - `simulated-city/weather/state`
  - `simulated-city/weather/events`
- Subscribes:
  - (none required in current outline)

### Agent: Observer (Rain Sensor)
- Publishes:
  - `simulated-city/observer/rain`
- Subscribes:
  - `simulated-city/weather/state`

### Agent: People (Mobility)
- Publishes:
  - `simulated-city/people/state`
  - `simulated-city/people/events`
- Subscribes:
  - `simulated-city/control/commands`

### Agent: Control Center
- Publishes:
  - `simulated-city/control/commands`
  - `simulated-city/control/decisions`
- Subscribes:
  - `simulated-city/observer/rain`
  - `simulated-city/people/state`
  - (shop locations are read from static config)

### Agent: Dashboard (read-only)
- Publishes:
  - (none)
- Subscribes:
  - `simulated-city/weather/state`
  - `simulated-city/people/state`
  - (shop locations are read from static config)
  - `simulated-city/control/commands` (monitoring/debug view only)

---

## 3) Configuration Parameters to Define

## MQTT/Broker
- `mqtt.active_profiles`
- `mqtt.profiles.<name>.host`
- `mqtt.profiles.<name>.port`
- `mqtt.profiles.<name>.tls`
- `mqtt.profiles.<name>.username_env` (if needed)
- `mqtt.profiles.<name>.password_env` (if needed)
- `mqtt.client_id_prefix`
- `mqtt.keepalive_s`
- `mqtt.base_topic`

## Simulation Timing
- `simulation.tick_s`
- `simulation.duration_s` (set to continuous run)
- `weather.sun_duration_s`
- `weather.rain_duration_s`

## Run Control
- `simulation.stop_mode` (manual stop via dedicated bottom notebook cell)

## Geographic Area and Locations
- `city.center_lat`
- `city.center_lon`
- `city.boundary_radius_m` (or bounding box)
- `shops.count`
- `shops.locations` (lat/lon list)

## People and Movement
- `people.max_count`
- `people.spawn_mode` (fixed count; always 5 at simulation start)
- `people.spawn_point_policy` (e.g., `center_fixed`)
- `people.speed_m_per_s`
- `people.random_walk_step_m`
- `people.arrival_threshold_m` (distance considered “arrived” at coffee shop)
- `people.name_pool`
- `people.color_palette`

## Randomness
- `simulation.random_seed` (optional; leave unset for non-deterministic runs)

## Decision/Control Parameters
- `control.nearest_shop_metric` (euclidean, haversine, projected meters)
- `control.target_selection_policy` (e.g., `fixed_per_rain_episode`)
- `control.recompute_interval_s` (decision/movement update interval; does not change target during rain when policy is fixed)
- `control.fallback_behavior_when_missing_data`

## Dashboard/Visualization
- `map.center_lat`
- `map.center_lon`
- `map.zoom`
- `map.theme_sun`
- `map.theme_rain`
- `map.refresh_on_events` (set to `people_movement` and `weather_state_change`)
- `dashboard.publish_enabled` (set to `false`)


---

## 4) Suggested Realistic Starting Values (MVP)

These are practical defaults for a workshop-scale simulation and can be tuned later.

## Core Simulation
- `people.max_count`: 5
- `people.spawn_mode`: fixed count `5`
- `people.spawn_point_policy`: `center_fixed`
- `simulation.tick_s`: 1.0
- `simulation.duration_s`: continuous
- `weather.sun_duration_s`: 20
- `weather.rain_duration_s`: 10
- `simulation.random_seed`: unset
- `control.target_selection_policy`: `fixed_per_rain_episode`
- `control.recompute_interval_s`: 1.0 (movement/decision updates; target remains fixed within each rain episode)
- `dashboard.publish_enabled`: `false`

## Movement
- `people.speed_m_per_s`: 1.2 (walking pace)
- `people.random_walk_step_m`: 3 to 8 per tick (if using step-based movement)
- `people.arrival_threshold_m`: 5

## Geography (Copenhagen center starter)
- `city.center_lat`: 55.6761
- `city.center_lon`: 12.5683
- `city.boundary_radius_m`: 800
- `shops.count`: 5
- `shops.locations`: fixed static coordinates in config
- `map.zoom`: 14
- `map.theme_sun`: `normal`
- `map.theme_rain`: `dark`
- `map.refresh_on_events`: [`people_movement`, `weather_state_change`]

## MQTT
- Primary workshop local profile: host `127.0.0.1`, port `1883`, tls `false`
- Keepalive: `60`
- Base topic: `simulated-city`

## Optional Environment Indicator
- `environment.rain_intensity_scale`: 0 to 1
- Start with sun = 0.0, rain = 0.8

---
