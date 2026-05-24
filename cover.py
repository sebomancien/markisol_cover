import logging

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.components.radio_frequency import async_send_command
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from rf_protocols import ModulationType, RadioFrequencyCommand

from .markisol import MarkisolCommand
from .remote   import Channel, Command, RemoteCommand

_LOGGER = logging.getLogger(__name__)

FREQUENCY = 433_920_000  # 433.92 MHz
REPEAT = 40

class _RFCommand(RadioFrequencyCommand):
    def __init__(self, cmd: MarkisolCommand) -> None:
        super().__init__(
            frequency=FREQUENCY,
            modulation=ModulationType.OOK,
            repeat_count=REPEAT,
        )
        self._cmd = cmd

    def get_raw_timings(self) -> list[int]:
        return self._cmd.encode()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarkisolCover(entry)])


class MarkisolCover(CoverEntity, RestoreEntity):
    _attr_assumed_state = True
    _attr_should_poll = False
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_is_closed: bool | None = None
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, entry: ConfigEntry) -> None:

        self._transmitter: str = entry.data["transmitter"]

        ch_num = entry.data["channel"]
        channel = Channel.ALL if ch_num == 0 else Channel(ch_num)

        def _make(cmd: Command) -> MarkisolCommand:
            data = RemoteCommand(
                remote_id=entry.data["remote_id"],
                channel=channel,
                command=cmd,
                model_id=entry.data["model_id"],
            ).encode()
            _LOGGER.debug("data32=0x%08X cmd=%s", data, cmd.name)
            return MarkisolCommand(data)

        self._open_cmd  = _make(Command.OPEN)
        self._close_cmd = _make(Command.CLOSE)
        self._stop_cmd  = _make(Command.STOP)
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.title

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._attr_is_closed = last.state == "closed"

    async def _send(self, cmd: MarkisolCommand) -> None:
        await async_send_command(self.hass, self._transmitter, _RFCommand(cmd))

    async def async_open_cover(self, **kwargs) -> None:
        await self._send(self._open_cmd)
        self._attr_is_closed = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs) -> None:
        await self._send(self._close_cmd)
        self._attr_is_closed = True
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs) -> None:
        await self._send(self._stop_cmd)
        self.async_write_ha_state()
