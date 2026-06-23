"""API commands for the phase: PT Cooling"""

import time
import logging

# params:
from functions import (
    Timer,
    ErrorState,
    value,
    valves_on,
    valves_off,
    pump_on,
    pump_off,
    heater_on,
    heater_off,
    set_heater_power,
    pulse_tube_on,
    pulse_tube_off,
    set_cold_cathode,
    warmup_heater_1_on,
    warmup_heater_1_off,
    warmup_heater_2_on,
    warmup_heater_2_off,
    circulation_turbo_pumps_on,
    circulation_turbo_pumps_off,
)
from configuration import service_booster_pump_available

# PT_COOLING


pt_p1_min_pressure = 5e-5  # bar
pt_cooling_max_pump_time = 24 * 3600  # sec
pt_cooling_target_pressure = 3e-6  # bar
pt_cooling_PPC_trigger_temperature = (
    15  # (Still) temperature to finalize PT cooling phase
)
pt_cooling_finalize_timeout = (
    10 * 3600
)  # Timeout to raise error if not proceeding PT cooling finalize phase

timer = Timer()
log = logging.getLogger(__name__)


def check_if_possible_state():
    if value("P1_PRESSURE") > pt_p1_min_pressure:
        error = "PT_Cooling " + check_if_possible_state.__name__
        error_message = "P1 too high to start PT cooling"
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)


def pt_on():
    log.info("PT Cooling: PT On: Turning on pulse tubes and heat switches")
    pulse_tube_on("PULSE_TUBE")
    heater_on(["HEATSWITCH_MXC", "HEATSWITCH_STILL"])
    timer.reset()
    while (
        value("P1_PRESSURE") > pt_cooling_target_pressure
        or value("50K_TEMPERATURE") > 85
        or value("4K_TEMPERATURE") > 50
        or value("STILL_TEMPERATURE") > 55
    ):
        time.sleep(60)
        if timer > pt_cooling_max_pump_time:
            error = "PT_Cooling " + pt_on.__name__
            if value("P1_PRESSURE") > pt_cooling_target_pressure:
                error_message = "P1 too high after PT cooling"
            elif value("50K_TEMPERATURE") > 85:
                error_message = "T50K too high after PT cooling"
            elif value("4K_TEMPERATURE") > 50:
                error_message = "T4K too high after PT cooling"
            elif value("STILL_TEMPERATURE") > 55:
                error_message = "Tstill too high after PT cooling"
            else:
                error_message = "Timeout in PT cooling"
            log.error(error + " msg:" + error_message)
            raise ErrorState(error, error_message)


def stop_vc_pumping():
    if service_booster_pump_available:
        log.info("PT Cooling: Stop VC Pumping: Turning off service pumps and valves")
        valves_off(["V101", "V104", "V105", "V107", "V106"])
        pump_off("R2")  # turn off service_rough_pump
        pump_off("B2")  # turn off service_booster_pump
    else:
        log.info("PT Cooling: Stop VC Pumping: Turning off valves")
        valves_off(["V101", "V112", "V114", "V105"])
        log.info(
            "PT Cooling: Stop VC Pumping: Turning off pumps service_rough_pump, circulation_booster_pump"
        )
        circulation_turbo_pumps_off("TURBO_PUMP")
        pump_off("R2")  # turn off service_rough_pump
    # wait for booster pumps to spin down
    time.sleep(1800)


def pt_cooling_finalize():
    # settling time before next phase (PPC)
    log.info("PT Cooling: PT Cooling finalize: Wait for Still to cool to 15 K")
    timer.reset()
    while (
        value("STILL_TEMPERATURE") > pt_cooling_PPC_trigger_temperature
        or value("4K_TEMPERATURE") > pt_cooling_PPC_trigger_temperature
    ):
        time.sleep(60)
        if timer > pt_cooling_finalize_timeout:
            error = "PT_Cooling " + pt_cooling_finalize.__name__
            if value("4K_TEMPERATURE") > pt_cooling_PPC_trigger_temperature:
                error_message = "T4K too high after PT cooling"
            elif value("STILL_TEMPERATURE") > pt_cooling_PPC_trigger_temperature:
                error_message = "Tstill too high after PT cooling"
            else:
                error_message = "Timeout in PT cooling finalize"
            log.error(error + " msg:" + error_message)
            raise ErrorState(error, error_message)

    log.info("PT Cooling: Ready for next phase")
