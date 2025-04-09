import base64
import json
import logging
import math
import secrets
import time

from . import RoborockCommand
from .containers import DeviceData, UserData
from .mqtt_manager import RoborockMqttManager
from .protocol import MessageParser, Utils
from .roborock_message import RoborockMessage, RoborockMessageProtocol
from .util import RoborockLoggerAdapter, get_next_int

_LOGGER = logging.getLogger(__name__)


class RoborockDevice:
    def __init__(self, user_data: UserData, device_info: DeviceData):
        self.user_data = user_data
        self.device_info = device_info
        self.data = None
        self._logger = RoborockLoggerAdapter(device_info.device.name, _LOGGER)
        self._mqtt_endpoint = base64.b64encode(Utils.md5(user_data.rriot.k.encode())[8:14]).decode()
        self._local_endpoint = "abc"
        self._nonce = secrets.token_bytes(16)
        self.manager = RoborockMqttManager()
        self.update_commands = self.determine_supported_commands()

    def determine_supported_commands(self):
        # All devices support these
        supported_commands = {
            RoborockCommand.GET_CONSUMABLE,
            RoborockCommand.GET_STATUS,
            RoborockCommand.GET_CLEAN_SUMMARY,
        }
        # Get what features we can from the feature_set info.

        # If a command is not described in feature_set, we should just add it anyways and then let it fail on the first call and remove it.
        robot_new_features = int(self.device_info.device.feature_set)
        new_feature_info_str = self.device_info.device.new_feature_set
        if 33554432 & int(robot_new_features):
            supported_commands.add(RoborockCommand.GET_DUST_COLLECTION_MODE)
        if 2 & int(new_feature_info_str[-8:], 16):
            # TODO: May not be needed as i think this can just be found in Status, but just POC
            supported_commands.add(RoborockCommand.APP_GET_CLEAN_ESTIMATE_INFO)
        return supported_commands

    async def connect(self):
        """Connect via MQTT and Local if possible."""
        await self.manager.subscribe(self.user_data, self.device_info, self.on_message)
        await self.update()

    async def update(self):
        for cmd in self.update_commands:
            await self.send_message(method=cmd)

    def _get_payload(
        self,
        method: RoborockCommand | str,
        params: list | dict | int | None = None,
        secured=False,
        use_cloud: bool = False,
    ):
        timestamp = math.floor(time.time())
        request_id = get_next_int(10000, 32767)
        inner = {
            "id": request_id,
            "method": method,
            "params": params or [],
        }
        if secured:
            inner["security"] = {
                "endpoint": self._mqtt_endpoint if use_cloud else self._local_endpoint,
                "nonce": self._nonce.hex().lower(),
            }
        payload = bytes(
            json.dumps(
                {
                    "dps": {"101": json.dumps(inner, separators=(",", ":"))},
                    "t": timestamp,
                },
                separators=(",", ":"),
            ).encode()
        )
        return request_id, timestamp, payload

    async def send_message(
        self, method: RoborockCommand | str, params: list | dict | int | None = None, use_cloud: bool = True
    ):
        request_id, timestamp, payload = self._get_payload(method, params, True, use_cloud)
        request_protocol = RoborockMessageProtocol.RPC_REQUEST
        roborock_message = RoborockMessage(timestamp=timestamp, protocol=request_protocol, payload=payload)

        local_key = self.device_info.device.local_key
        msg = MessageParser.build(roborock_message, local_key, False)
        if use_cloud:
            await self.manager.publish(self.user_data, self.device_info, msg)
        else:
            # Handle doing local commands
            pass

    def on_message(self, message: RoborockMessage):
        # If message is command not supported - remove from self.update_commands

        # If message is an error - log it?

        # If message is 'ok' - ignore it

        # If message is anything else - store ids, and map back to id to determine message type.
        # Then update self.data

        # If we haven't received a message in X seconds, the device is likely offline. I think we can continue the connection,
        # but we should have some way to mark ourselves as unavailable.

        # This should also probably be split with on_cloud_message and on_local_message.
        print(message)
