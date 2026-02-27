from __future__ import annotations

import json
import logging
import socket
import ssl
from typing import TYPE_CHECKING
import threading

from .config import MqttConfig

if TYPE_CHECKING:
    import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttConnector:
    """MQTT client with automatic reconnection."""

    def __init__(self, cfg: MqttConfig, *, client_id_suffix: str | None = None):
        try:
            import paho.mqtt.client as mqtt
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "paho-mqtt is required to use simulated_city.mqtt. "
                "Install dependencies (e.g. `pip install -e .`) and try again."
            ) from e

        self.cfg = cfg
        self._client_id = _make_client_id(cfg.client_id_prefix, client_id_suffix)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self._client_id)
        self.connected = threading.Event()

        if cfg.username is not None:
            self.client.username_pw_set(cfg.username, password=cfg.password)

        if cfg.tls:
            context = ssl.create_default_context()
            self.client.tls_set_context(context)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.cfg.host}:{self.cfg.port}")
            self.connected.set()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_disconnect(self, client, userdata, flags, reason, properties):
        logger.warning(f"Disconnected from MQTT broker (reason={reason}). Reconnecting...")
        self.connected.clear()

    def connect(self):
        """Connect the client and start the network loop."""
        try:
            self.client.connect(self.cfg.host, self.cfg.port, keepalive=self.cfg.keepalive_s)
            self.client.loop_start()
        except (OSError, socket.gaierror, ssl.SSLError) as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect the client and stop the network loop."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker.")

    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait for the client to connect."""
        return self.connected.wait(timeout)


class MqttPublisher:
    """A simple MQTT publisher."""

    def __init__(self, connector: MqttConnector):
        self.client = connector.client

    def publish_json(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publish a JSON string to a topic."""
        if not self.client.is_connected():
             logger.warning("MQTT client not connected. Message may not be published.")
        result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
        # For QoS > 0, this will block until the message is sent.
        # For QoS = 0, it returns immediately.
        if qos > 0:
            result.wait_for_publish()
        return result


def connect_mqtt(mqtt_config: MqttConfig, *, client_id_suffix: str | None = None, timeout_s: float = 10.0):
    """Connect to MQTT and return a connected paho client.

    This is a beginner-friendly wrapper around ``MqttConnector``.
    """

    connector = MqttConnector(mqtt_config, client_id_suffix=client_id_suffix)
    connector.connect()

    if not connector.wait_for_connection(timeout=timeout_s):
        connector.disconnect()
        raise RuntimeError(
            f"Failed to connect to MQTT broker at {mqtt_config.host}:{mqtt_config.port}"
        )

    # Keep a reference so callers can optionally close via
    # ``client._simcity_connector.disconnect()`` in notebooks.
    setattr(connector.client, "_simcity_connector", connector)
    return connector.client


def publish_json_checked(client, topic: str, data: dict, *, qos: int = 1, retain: bool = False, timeout_s: float = 5.0):
    """Publish JSON and verify broker accepted the message.

    Raises ``RuntimeError`` when publish fails.
    """

    payload = json.dumps(data)
    info = client.publish(topic, payload=payload, qos=qos, retain=retain)

    if info.rc != 0:
        raise RuntimeError(f"MQTT publish failed (rc={info.rc}) for topic '{topic}'")

    info.wait_for_publish(timeout=timeout_s)
    if not info.is_published():
        raise RuntimeError(f"MQTT publish timed out for topic '{topic}'")

    return info


def _make_client_id(prefix: str, suffix: str | None) -> str:
    """Create a client ID from a prefix and an optional suffix."""
    safe_prefix = prefix.strip() or "simcity"
    if suffix:
        return f"{safe_prefix}-{suffix}"
    return safe_prefix
