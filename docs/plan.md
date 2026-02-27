## Plan: Multi-Agent MQTT Notebook Workshop Rollout (DRAFT)

This phased plan follows your clarified design in [docs/concepts.md](docs/concepts.md), uses separate notebooks per agent, and keeps MQTT as the only integration path between agents and dashboard. Based on your decisions, Phase 4 adds a People/Transport agent, we introduce helper wrappers so notebooks can use connect_mqtt and publish_json_checked consistently, and we default development verification to a local broker profile. The sequence starts with a runnable single-agent baseline, then progressively adds config discipline, publish/subscribe messaging, and map visualization, ending with hardening and documentation/test alignment so students can validate structure and behavior reliably.

**Phase 1: Minimal working example (one agent, basic logic)**
- New files
  - Create one notebook in [notebooks](notebooks), e.g. notebooks/agent_weather.ipynb
  - Update design notes if needed in [docs/concepts.md](docs/concepts.md) to reflect minimal message schema used in Phase 1
- Tests/Verification
  - python scripts/verify_setup.py
  - python scripts/validate_structure.py
  - Manual: run the notebook loop locally and confirm deterministic basic logic output in cell output
- Investigation before next phase
  - Confirm minimal payload contract (fields, cadence, topic naming prefix) that all later phases will reuse
  - Confirm notebook run/stop pattern for students (loop duration, interrupt behavior)
- Dependencies
  - No new package required if notebooks extra is already installed
  - Required environment baseline: jupyterlab and ipykernel available from [pyproject.toml](pyproject.toml)

**Phase 2: Add configuration file usage (config.yaml-driven behavior)**
- New files
  - Modify [config.yaml](config.yaml) to include phase-specific topic and timing defaults for the first agent
  - Modify notebook created in Phase 1 to load settings through [src/simulated_city/config.py](src/simulated_city/config.py)
  - If needed, align config docs in [docs/config.md](docs/config.md) and setup notes in [docs/setup.md](docs/setup.md)
- Tests/Verification
  - python -m pytest tests/test_config.py -v
  - python scripts/verify_setup.py
  - Manual: run notebook from notebooks folder and confirm config auto-discovery still works
- Investigation before next phase
  - Decide stable config keys for topic names and publish interval to prevent later notebook churn
  - Validate local-only active profile strategy for development
- Dependencies
  - No new package expected (PyYAML and python-dotenv already present in [pyproject.toml](pyproject.toml))

**Phase 3: Add MQTT publishing from first agent**
- New files
  - Update [src/simulated_city/mqtt.py](src/simulated_city/mqtt.py) with helper wrappers (connect_mqtt, publish_json_checked) while preserving existing class API
  - Update notebook from Phase 1 to publish JSON messages to configured topic
  - Update MQTT docs in [docs/mqtt.md](docs/mqtt.md) and/or exercise flow in [docs/exercises.md](docs/exercises.md)
- Tests/Verification
  - python -m pytest tests/test_smoke.py -v
  - python -m pytest tests/test_mqtt_profiles.py -v
  - python scripts/validate_structure.py
  - Manual: subscribe with a temporary client and verify messages arrive on the expected topic
- Investigation before next phase
  - Confirm publish acknowledgment/verification behavior expectations for workshop reliability
  - Confirm fallback behavior when broker unavailable (retry vs fail-fast for teaching context)
- Dependencies
  - No new package expected (paho-mqtt already present)

**Phase 4: Add second agent with MQTT subscription (People/Transport)**
- New files
  - Create second notebook in [notebooks](notebooks), e.g. notebooks/agent_people.ipynb
  - Update [docs/concepts.md](docs/concepts.md) with explicit weather-to-people topic contract and derived output topic
  - Extend [docs/exercises.md](docs/exercises.md) with two-agent run order
- Tests/Verification
  - python scripts/validate_structure.py
  - python -m pytest tests/test_smoke.py -v
  - Manual: run both notebooks concurrently; verify second agent consumes weather messages and publishes derived state
- Investigation before next phase
  - Validate message schema compatibility and timestamp handling between agents
  - Validate notebook startup order requirements and reconnection behavior
- Dependencies
  - No new package expected

**Phase 5: Add dashboard visualization**
- New files
  - Create dashboard notebook in [notebooks](notebooks), e.g. notebooks/dashboard_city.ipynb
  - Use map helpers/patterns from [src/simulated_city/maplibre_live.py](src/simulated_city/maplibre_live.py) and guidance in [docs/maplibre_anymap.md](docs/maplibre_anymap.md)
  - Update exercise instructions in [docs/exercises.md](docs/exercises.md)
- Tests/Verification
  - python -m pytest tests/test_maplibre_live.py -v
  - python scripts/validate_structure.py
  - Manual: run agents + dashboard together, verify live updates and style state changes (including rain/dark mode behavior if included in current schema)
- Investigation before next phase
  - Confirm minimal visual layers needed for MVP dashboard (avoid extra UX beyond design)
  - Confirm performance/cadence limits for notebook rendering
- Dependencies
  - anymap-ts[all] and jupyterlab should be installed via notebooks extra in [pyproject.toml](pyproject.toml)
  - No folium/plotly/matplotlib for live mapping usage

**Phase 6: Stabilization, documentation sync, and end-to-end validation**
- New files
  - Update scenario docs for final workflow in [docs/overview.md](docs/overview.md), [docs/testing.md](docs/testing.md), and [README.md](README.md) if notebook names/run steps changed
  - Add or adjust focused tests only where behavior changed (likely MQTT helper API tests and any config/topic contract tests in [tests](tests))
- Tests/Verification
  - python scripts/verify_setup.py
  - python scripts/validate_structure.py
  - python -m pytest
  - Manual: cold-start runbook test (fresh kernel order: weather agent, people agent, dashboard)
- Investigation
  - Confirm all docs and notebook names are consistent across repo references
  - Confirm beginner-path clarity: install, run order, expected outputs, troubleshooting
- Dependencies
  - No additional packages planned; keep dependency surface minimal

**Verification**
- Phase gate rule before moving on: pass verify_setup, pass validate_structure, pass phase-targeted pytest, then perform one manual runtime check in notebooks.
- Default development broker profile: local only in [config.yaml](config.yaml) for predictable workshop execution.

**Decisions**
- Second agent in Phase 4 is People/Transport.
- MQTT helper wrappers are added before notebook messaging phases rely on them.
- Local broker profile is the default for development verification.
