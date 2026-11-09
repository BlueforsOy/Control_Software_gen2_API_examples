"""API commands for the phase: Condensing"""

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
from configuration import service_booster_pump_available, number_of_circulation_turbo_pumps

initial_tank_pressure = (
    0.720  # How much mixture is in the system, given in configuration
)
condensing_vc_pressure_limit = (
    8e-8  # Maximum allowed Vacuum can pressure to start condensing (in bar)
)
condensing_trigger_heatswitches = (
    0.08  # How much mixture will be condensed before heat switches go off
)
condensing_system_blocked_timer = 2 * 3600  # Timer to stop condensing if not proceeding
condensing_pressure_drop_max_time = 7200  # default value TBD
condensing_pressure_difference_max_time = 3600  # default value TBD
condensing_still_heating_power = 0.008  # in watt
CondensingLineValve504H = True
CondensingLineValve505H = False
BypassLN2Trap = False
# Select only one LN2 trap
LN2Trap1Enabled = True
LN2Trap2Enabled = False  # only available for industrial GHS version

timer1 = Timer()
timer2 = Timer()
timer3 = Timer()
log = logging.getLogger(__name__)


#
# Condensing script for SD/LD/XLD systems
#


def check_if_possible_state():
    # checks that ok to transition to this state
    if not value("PULSE_TUBE_ENABLED"):
        error = "Condensing " + check_if_possible_state.__name__
        error_message = "Pulse tube is not running"
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)
    # Following condition system type dependent? (LD vs XLD1000)
    if value("P5_PRESSURE") < initial_tank_pressure:
        error = "Condensing " + check_if_possible_state.__name__
        error_message = "Helium tank pressure is low, check that mixture is in the tank"
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)
    if value("P1_PRESSURE") > condensing_vc_pressure_limit:
        error = "Condensing " + check_if_possible_state.__name__
        error_message = "Vacuum can pressure is too high"
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)
    if (
        value("4K_TEMPERATURE") > 4.6
        or value("STILL_TEMPERATURE") > 5.3
        or value("MXC_TEMPERATURE") > 6
    ):
        error = "Condensing " + check_if_possible_state.__name__
        error_message = "System too warm to condense"
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)


def initial_settings():
    # initial settings for the state
    heater_on(["HEATSWITCH_MXC", "HEATSWITCH_STILL"])
    circulation_turbo_pumps_off("TURBO_PUMP")
    while value("B1A_SPEED") > 200:
        log.info("Waiting for circulation booster pump to slow down")
        time.sleep(15)


def close_critical_valves():
    # make sure critical valves and pumps are closed/turned off
    if service_booster_pump_available:
        pump_off("B2")  # turn off service_booster_pump
        valves_off(["V106", "V107", "V104"])
    else:
        valves_off(["V105"])
    pump_off("R2")  # turn off service_rough_pump
    valves_off(
        [
            "V112",
            "V113",
            "V114",
            "V203",
            "V004",
            "V003",
            "V005",
            "V303",
            "V306",
            "V403",
            "V404",
            "V406",
            "V502H",
            "V101",
            "V104",
        ]
    )


def condensing_init():
    log.info("Condensing: Condensing Init: Initializing circulation")

    valves_on(["V501H", "V503H", "V302", "V304"])
    if CondensingLineValve504H:
        valves_on(["V504H"])
    elif CondensingLineValve505H:
        valves_on(["V505H"])
    else:
        error = "Condensing " + condensing_init.__name__
        error_message = "To proceed with condensing, enable CondensingLine504H or CondensingLine505H"  # This if statement segment may be removed
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)
    if BypassLN2Trap:
        valves_on(["V403"])
    elif LN2Trap1Enabled:
        valves_on(["V401", "V402"])
    elif LN2Trap2Enabled:
        valves_on(["V405", "V407"])
    else:
        error = "Condensing " + condensing_init.__name__
        error_message = "Select a LN2 trap ready to use or enable BypassLN2Trap"  # This if statement segment may be removed
        log.error(error + " msg:" + error_message)
        raise ErrorState(error, error_message)

    pump_on("COM")  # turn on helium_compressor
    pump_on("R1A")  # turn on circulation_rough_pump
    time.sleep(10)
    valves_on(["V202", "V001"])
    time.sleep(60)
    valves_on(["V201G"])
    valves_off(["V202"])
    # start condensing


def condensing_high_p5():
    log.info("Condensing: Condensing High P5: Entering the P5 > 250 condensing loop")
    heat_switch_trigger_pressure = (
        value("P5_PRESSURE") - condensing_trigger_heatswitches
    )

    while value("P5_PRESSURE") > 0.250:
        valves_on(["V003"])
        valves_off(["V001"])
        timer1.reset()

        while value("P4_PRESSURE") < 0.900:
            time.sleep(0.5)

            if timer1 > 180 and value("P5_PRESSURE") > 0.300:
                error = "Condensing " + condensing_high_p5.__name__
                error_message = "Needle valve set too tight, check adjustment"
                log.error(error + " msg:" + error_message)
                log.info("Turn off V003 and turning on V001")
                valves_off(["V003"])
                valves_on(["V001"])
                raise ErrorState(error, error_message)

            if timer1 > 180:  # Old state 413
                valves_off(["V003"])
                valves_on(["V001"])
                error = "Condensing " + condensing_high_p5.__name__
                error_message = (
                    "Condensing not working"  # This if statement segment may be removed
                )
                log.error(error + " msg:" + error_message)
                raise ErrorState(
                    error, error_message
                )  # In original script we go to the beginning of the 'while p5>250' loop

        # Once above 900 mbar, stop mixture intake from the tank
        if value("P4_PRESSURE") > 0.900:
            valves_off(["V003"])
            valves_on(["V001"])
            timer2.reset()
            time.sleep(10)

            # Evaluate if heat switches can be turned off:
            if (
                value("HEATSWITCH_STILL_ENABLED")
                and value("HEATSWITCH_MXC_ENABLED")
                and value("P5_PRESSURE") < heat_switch_trigger_pressure
            ):
                heater_off(["HEATSWITCH_MXC"])

            if (
                value("HEATSWITCH_STILL_ENABLED")
                and value("P5_PRESSURE") < heat_switch_trigger_pressure
                and value("STILL_TEMPERATURE") < (value("4K_TEMPERATURE") + 2)
            ):
                heater_off(["HEATSWITCH_STILL"])

            while value("P4_PRESSURE") > 0.600:
                time.sleep(2)
                if (
                    timer2 > condensing_system_blocked_timer
                ):  # If p4 does not drop below threshold, something is wrong
                    error = "Condensing " + condensing_high_p5.__name__
                    error_message = "System not condensing, read manual"
                    log.error(error + " msg:" + error_message)
                    log.info("Error in condensing: P4 doesn't decrease fast enough")
                    log.info(
                        "Leave system in a safe state, recovering mixture. Turning off COM (helium compressor) and valves V503H, V402, V403, V407"
                    )
                    pump_off("COM")  # turn off helium_compressor
                    valves_off(["V503H", "V402", "V403", "V407"])
                    log.info("Turning on V202, V203, V502H, V005")
                    valves_on(["V202", "V203", "V502H", "V005"])
                    time.sleep(10)
                    log.info("Turning off valve V501H")
                    valves_off(
                        ["V501H"]
                    )  # Could be appended with a procedure to collect all condensed mixture
                    raise ErrorState(error, error_message)

    valves_off(["V003"])
    valves_on(["V001"])


def condensing_low_p5():
    # Condense via V004 instead of needle valve V003 when p5 < 250 mbar
    log.info(
        "Condensing: Condensing Low P5: Entering the P5 > 50 valve V004 condensing loop"
    )
    timer2.reset()

    while value("P5_PRESSURE") > 0.050:
        timer3.reset()
        valves_on(["V004"])
        valves_off(["V001"])

        while value("P4_PRESSURE") < 0.900 and timer3 < 60:
            time.sleep(0.5)

        if value("P4_PRESSURE") > 0.900:
            valves_on(["V001"])
            valves_off(["V004"])
            time.sleep(2)

            while value("P4_PRESSURE") > 0.600:
                time.sleep(2)
                if (
                    timer2 > condensing_system_blocked_timer
                ):  # If p4 does not drop below threshold, something is wrong
                    error = "Condensing " + condensing_high_p5.__name__
                    error_message = "System not condensing, read manual"
                    log.error(error + " msg:" + error_message)
                    log.info("Error in condensing: P4 doesn't decrease fast enough")
                    log.info(
                        "Leave system in a safe state, recovering mixture. Turning off COM (helium compressor) and valves V503H, V402, V403, V407"
                    )
                    pump_off("COM")  # turn off helium_compressor
                    valves_off(["V503H", "V402", "V403", "V407"])
                    log.info("Turning on V202, V203, V502H, V005")
                    valves_on(["V202", "V203", "V502H", "V005"])
                    time.sleep(10)
                    log.info("Turn off valve V501H")
                    valves_off(
                        ["V501H"]
                    )  # Could be appended with a procedure to collect all condensed mixture
                    raise ErrorState(error, error_message)

    valves_off(["V004"])
    valves_on(["V001"])


def condensing_finalize():
    log.info("Condensing: Condensing Finalize: Entering condensing_finalize()")
    log.info(
        "Condensing: Condensing Finalize: Tank pressure below 50 mbar, pump remaining gas into circulation"
    )
    valves_on(["V004"])
    time.sleep(420)
    valves_off(["V004"])

    log.info("Condensing: Condensing Finalize: Start normal circulation")
    pump_off("COM")  # turn off helium_compressor

    timer1.reset()
    while value("P3_PRESSURE") > 1.000:
        time.sleep(2)
        if timer1 > condensing_pressure_drop_max_time:
            error = "Condensing " + condensing_finalize.__name__
            error_message = "Condensing pressure not dropping"
            log.error(error + " msg:" + error_message)
            raise ErrorState(error, error_message)

    valves_off(["V501H", "V503H"])
    time.sleep(2)

    timer1.reset()
    while value("P3_PRESSURE") > value("P4_PRESSURE"):
        time.sleep(2)
        log.info("Waiting for p3 to drop below p4")
        if timer1 > condensing_pressure_difference_max_time:
            error = "Condensing " + condensing_finalize.__name__
            error_message = "p3-p4 pressure difference not decreasing"
            log.error(error + " msg:" + error_message)
            raise ErrorState(error, error_message)

    valves_on(["V502H"])
    time.sleep(180)

    timer1.reset()
    while value("P3_PRESSURE") > 0.900:
        time.sleep(5)
        if timer1 > condensing_pressure_drop_max_time:
            error = "Condensing " + condensing_finalize.__name__
            error_message = "p3 pressure not dropping, turbo pump cannot be started"
            log.error(error + " msg:" + error_message)
            raise ErrorState(error, error_message)

    circulation_turbo_pumps_on("TURBO_PUMP")
    # Still heater power for the first 30 minutes depends on the number of circulation turbo pumps
    if number_of_circulation_turbo_pumps == 2:
        still_heater_power = 0.020
    elif number_of_circulation_turbo_pumps >= 3:
        still_heater_power = 0.030
    else:
        still_heater_power = 0.012
    set_heater_power(("bftc-device-1", "3"), still_heater_power)
    heater_on(["STILL_HEATER"])
    log.info(f"Condensing: Apply still heater power {still_heater_power * 1e3:.0f} mW for 30min")
    try:
        time.sleep(1800)
    finally:
        log.info("Condensing: Apply default still heater power")
        set_heater_power(("bftc-device-1", "3"), condensing_still_heating_power)
    log.info("System cooling to base temperature")
