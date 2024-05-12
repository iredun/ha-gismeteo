# pylint: disable=protected-access,redefined-outer-name
"""Tests for Gismeteo integration."""

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gismeteo.const import CONF_PLATFORM_FORMAT, DOMAIN
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import FAKE_CONFIG


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with (
        patch(
            "custom_components.gismeteo.async_setup",
            return_value=True,
        ),
        patch(
            "custom_components.gismeteo.async_setup_entry",
            return_value=True,
        ),
    ):
        yield


# Here we simulate a successful config flow from the backend.
# Note that we use the `bypass_get_data` fixture here because
# we want the config flow validation to succeed during the test.
async def test_successful_config_flow(hass: HomeAssistant, bypass_get_data):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=FAKE_CONFIG
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == FAKE_CONFIG[CONF_NAME]
    assert result["data"] == FAKE_CONFIG
    assert result["result"]


# In this case, we want to simulate a failure during the config flow.
# We use the `error_on_get_data` mock instead of `bypass_get_data`
# (note the function parameters) to raise an Exception during
# validation of the input config.
async def test_failed_config_flow(hass: HomeAssistant, error_on_get_data):
    """Test a failed config flow due to credential validation failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=FAKE_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


# Our config flow also has an options flow, so we must test it as well.
async def test_options_flow(hass: HomeAssistant):
    """Test an options flow."""
    # Create a new MockConfigEntry and add to HASS (we're bypassing config
    # flow entirely)
    entry = MockConfigEntry(domain=DOMAIN, data=FAKE_CONFIG, entry_id="test")
    entry.add_to_hass(hass)

    # Initialize an options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    # Verify that the first options step is a user form
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Enter some fake data into the form
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_PLATFORM_FORMAT.format(Platform.SENSOR): False},
    )

    # Verify that the flow finishes
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == FAKE_CONFIG[CONF_NAME]

    # Verify that the options were updated
    assert entry.options == {
        CONF_PLATFORM_FORMAT.format(Platform.SENSOR): False,
    }


async def test_options_flow_fail(hass: HomeAssistant):
    """Test an options flow."""
    # Create a new MockConfigEntry and add to HASS (we're bypassing config
    # flow entirely)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=FAKE_CONFIG,
        entry_id="test",
        source=config_entries.SOURCE_IMPORT,
    )
    entry.add_to_hass(hass)

    # Initialize an options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "no_options_available"
