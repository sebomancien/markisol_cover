import voluptuous as vol

from homeassistant.components.radio_frequency import ModulationType, async_get_transmitters
from homeassistant.config_entries import ConfigFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

CONF_TRANSMITTER = "transmitter"
CONF_REMOTE_ID = "remote_id"
CONF_CHANNEL = "channel"
CONF_MODEL_ID = "model_id"
FREQUENCY = 433_920_000  # 433.92 MHz
DEFAULT_MODEL_ID = 0x01

_CHANNEL_OPTIONS = [
    selector.SelectOptionDict(value="1", label="Channel 1"),
    selector.SelectOptionDict(value="2", label="Channel 2"),
    selector.SelectOptionDict(value="3", label="Channel 3"),
    selector.SelectOptionDict(value="4", label="Channel 4"),
    selector.SelectOptionDict(value="5", label="Channel 5"),
    selector.SelectOptionDict(value="0", label="All channels"),
]


class MarkisolCoverConfigFlow(ConfigFlow, domain="markisol_cover"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                remote_id = int(user_input[CONF_REMOTE_ID], 16)
                if not 0 <= remote_id <= 0xFFFF:
                    raise ValueError
            except ValueError:
                errors[CONF_REMOTE_ID] = "invalid_remote_id"

            try:
                model_id = int(user_input[CONF_MODEL_ID], 16)
                if not 0 <= model_id <= 0xFF:
                    raise ValueError
            except ValueError:
                errors[CONF_MODEL_ID] = "invalid_model_id"

            if not errors:
                ch = int(user_input[CONF_CHANNEL])
                ch_label = "All" if ch == 0 else f"Ch{ch}"
                title = f"Markisol {user_input[CONF_REMOTE_ID].upper()} {ch_label}"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_TRANSMITTER: user_input[CONF_TRANSMITTER],
                        CONF_REMOTE_ID: remote_id,
                        CONF_CHANNEL: ch,
                        CONF_MODEL_ID: model_id,
                    },
                )

        try:
            transmitters = async_get_transmitters(self.hass, FREQUENCY, ModulationType.OOK)
        except HomeAssistantError:
            return self.async_abort(reason="no_transmitters")

        if not transmitters:
            return self.async_abort(reason="no_transmitters")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRANSMITTER): selector.EntitySelector(
                        selector.EntitySelectorConfig(include_entities=transmitters)
                    ),
                    vol.Required(CONF_REMOTE_ID): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_MODEL_ID, default=format(DEFAULT_MODEL_ID, "02X")): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_CHANNEL, default="1"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_CHANNEL_OPTIONS,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )
