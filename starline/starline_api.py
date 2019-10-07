"""Data StarLine API."""
import logging
from typing import Dict, List, Callable, Optional, Any
from .base_api import BaseApi
from .device import StarlineDevice

_LOGGER = logging.getLogger(__name__)


class StarlineApi(BaseApi):
    """Data StarLine API class."""

    def __init__(self, user_id: str, slnet_token: str):
        """Constructor."""
        super().__init__()
        self._user_id = user_id
        self._slnet_token = slnet_token
        self._devices: Dict[str, StarlineDevice] = {}
        self._update_listeners: List[Callable] = []

    def _call_listeners(self) -> None:
        """Call listeners for update notifications."""
        for listener in self._update_listeners:
            listener()

    # TODO: Возможно это надо теперь в ХА делать
    def add_update_listener(self, listener: Callable) -> None:
        """Add a listener for update notifications."""
        self._update_listeners.append(listener)

    async def update(self, unused=None) -> None:
        """Update StarLine data."""
        devices = await self.get_user_info()

        for device_data in devices:
            device_id = str(device_data["device_id"])
            if device_id not in self._devices:
                self._devices[device_id] = StarlineDevice()
            self._devices[device_id].update(device_data)

        self._call_listeners()

    @property
    def devices(self):
        """Devices list."""
        return self._devices

    async def get_user_info(self) -> Optional[List[Dict[str, Any]]]:
        """Get user information."""

        # TODO: handle {'code': 500, 'codestring': 'Bad user id'}
        url = "https://developer.starline.ru/json/v2/user/{}/user_info".format(
            self._user_id
        )
        headers = {"Cookie": "slnet=" + self._slnet_token}
        response = await self.get(url, headers=headers)

        code = int(response["code"])
        if code == 200:
            return response["devices"] + response["shared_devices"]
        return None

    async def set_car_state(self, device_id: str, name: str, state: bool):
        """Set car state information."""
        _LOGGER.debug("Setting car %s state: %s=%d", device_id, name, state)
        url = "https://developer.starline.ru/json/v1/device/{}/set_param".format(
            device_id
        )
        data = {"type": name, name: 1 if state else 0}
        headers = {"Cookie": "slnet=" + self._slnet_token}
        response = await self.post(url, json=data, headers=headers)

        code = int(response["code"])
        if code == 200:
            self._devices[device_id].update_car_state(response)
            self._call_listeners()
            return response
        return None