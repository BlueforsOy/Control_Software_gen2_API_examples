"""API commands for the phase: Warm System"""

import time
import logging

# params:
from functions import Timer, ErrorState, value, valves_on, valves_off, pump_on, pump_off, \
    heater_on, heater_off, set_heater_power, pulse_tube_on, pulse_tube_off, set_cold_cathode, \
    warmup_heater_1_on, warmup_heater_1_off, warmup_heater_2_on, warmup_heater_2_off, \
    circulation_turbo_pumps_on, circulation_turbo_pumps_off

service_empty_pressure = 0.01 # bar
warmup_system_wait_stop_cooling = 900 # s
warmup_system_condensing_pressure_limit_in_collect_mixture = 0.05 # bar
warmup_system_collect_mixture_extra_time_limit = 1800
warmup_system_soft_vc_cycles = 2
warmup_system_p2_pressure_limit_mixture_in_tank = 0.05e-3
warmup_system_p5_pressure_limit_mixture_in_tank = 0.77
warmup_system_collect_mixture_max_time = 10 * 3600  # (?)
warmup_system_tank_pressure_stabilization_time = 1800
warmup_system_pressure_stabilization_sq_limit = 0.000005
warmup_system_tank_pressure_stabilization_max_time = 10 * 3600  # (?)
t_4k_upper_heater_limit = 300
warmup_system_warmup_max_time = 36 * 3600  # (?)

timer = Timer()
log = logging.getLogger(__name__)


#

# def check_if_possible_state():
# Checks that ok to transition to this state
def check_if_possible_state():
    # Check that the service line is empty
    if value('P6_PRESSURE') > service_empty_pressure:
        error_message = "WARMUP_SYSTEM_SERVICE_LINE_INIT_PRESSURE_HIGH"
        error = "Warmup System" + check_if_possible_state.__name__
        log.error(error + ' msg:' + error_message)
        raise ErrorState(error, error_message)


def initial_settings():
    if value('P1_ENABLED'):
        set_cold_cathode('plc.IO.P1')
        time.sleep(5)
        # double check that pressure gauge p1 cold cathode is inactive:
        if value('P1_ENABLED'):
            error_message = "Pressure gauge p1 high vacuum measurement is enabled, please check"
            error = 'Pump VC ' + initial_settings.__name__
            log.error(error + ' msg:' + error_message)
            raise ErrorState(error, error_message)


def stop_cooling():
    # Initial settings for the state
    valves_on(['V005'])
    valves_off(['V402','V403','V407'])
    circulation_turbo_pumps_off('TURBO_PUMP')
    pulse_tube_off('PULSE_TUBE')
    heater_off(['STILL_HEATER'])
    time.sleep(warmup_system_wait_stop_cooling)


def collect_mixture():
    log.info('Warm System: Collect Mixture: Entering collect_mixture()')
    log.info('Warm System: Collect Mixture: Checking that condensing pressure drops')
    # check condensing pressure dropped
    mix_timer = Timer()
    while value('P3_PRESSURE') > warmup_system_condensing_pressure_limit_in_collect_mixture and \
            mix_timer < warmup_system_collect_mixture_extra_time_limit:
        # not all collected, continue collecting
        time.sleep(30)

    # Pump cond-side and trap empty
    valves_on(['V203'])

    log.info('Warm System: Collect Mixture: Softening vacuum n times')
    # Soften vacuum N times
    for _ in range(warmup_system_soft_vc_cycles):
        valves_on(['V110'])
        time.sleep(5)
        valves_off(['V110'])
        time.sleep(5)
        valves_on(['V101', 'V104'])
        time.sleep(5)
        valves_off(['V101', 'V104'])

    # Turn on 4K heater
    # This turns on a heater with a specific heating power
    warmup_heater_1_on('4K_HEATER_1_ENABLED')

    # collect rest of mixture
    log.info('Warm System: Collect Mixture: Collecting the rest of the mixture')
    timer.reset()
    while value('P2_PRESSURE') > warmup_system_p2_pressure_limit_mixture_in_tank \
            or value('P5_PRESSURE') < warmup_system_p5_pressure_limit_mixture_in_tank:
        time.sleep(5)
        # check if too much time elapsed
        if timer > warmup_system_collect_mixture_max_time:
            error_message = "WARMUP_SYSTEM_TOO_LONG_COLLECTING_MIXTURE"
            error = "Warmup System" + collect_mixture.__name__
            log.error(error + ' msg:' + error_message)
            raise ErrorState(error, error_message)

        # check 4K flange not too hot
        if value('4K_TEMPERATURE') > t_4k_upper_heater_limit:
            warmup_heater_1_off('4K_HEATER_1_ENABLED')
            time.sleep(5)

        # pressures low enough for after collection

    # check pressures are stabilized
    last_p5 = value('P5_PRESSURE')  # Should this be updated in the while loop?
    log.info('Warm System: Wait for checking tank pressure stability')
    time.sleep(warmup_system_tank_pressure_stabilization_time)
    timer.reset()
    while (value('P5_PRESSURE') - last_p5) ** 2 > warmup_system_pressure_stabilization_sq_limit:
        last_p5 = value('P5_PRESSURE')
        log.info('Warm System: Collect Mixture: updating p5 value for checking tank pressure stability')
        time.sleep(warmup_system_tank_pressure_stabilization_time)
        # Should this be WARMUP_SYSTEM_TANK_PRESSURE_STABILIZATION_MAX_TIME?
        if timer > warmup_system_tank_pressure_stabilization_max_time:
            error_message = "WARMUP_SYSTEM_TOO_LONG_STABILIZING_TANK_PRESSURE"
            error = "Warmup System" + collect_mixture.__name__
            log.error(error + ' msg:' + error_message)
            raise ErrorState(error, error_message)


def stop_pumping():
    log.info('Warm System: Stop Pumping: Entering stop_pumping()')
    valves_off(['V401','V405'])
    time.sleep(10)
    valves_off(['V502H'])
    time.sleep(10)
    valves_off(['V203'])
    time.sleep(10)
    valves_off(['V201G'])
    time.sleep(10)
    valves_off(['V001'])
    time.sleep(10)
    valves_off(['V302'])
    time.sleep(10)
    pump_off('R1A') # turn off circulation_rough_pump
    valves_off(['V304'])
    time.sleep(10)
    valves_off(['V005'])
    time.sleep(10)

def wait_until_warm():
    log.info('Warm System: Wait Until Warm: Waiting for t_4K to rise above t_4k_upper_heater_limit')
    timer.reset()

    while value('STILL_TEMPERATURE') < 290:
        warmup_heater_1_on('4K_HEATER_1_ENABLED')
        time.sleep(30)
        if value('4K_TEMPERATURE') > t_4k_upper_heater_limit:
            warmup_heater_1_off('4K_HEATER_1_ENABLED')
            # Check if too much time has elapsed
            time.sleep(60)

        if timer > warmup_system_warmup_max_time:
            error_message = "WARMUP_SYSTEM_TOO_LONG_WARMING_UP"
            warmup_heater_1_off('4K_HEATER_1_ENABLED')
            error = "Warmup System" + wait_until_warm.__name__
            log.error(error + ' msg:' + error_message)
            warmup_heater_1_off('4K_HEATER_1_ENABLED')
            raise ErrorState(error, error_message)

    warmup_heater_1_off('4K_HEATER_1_ENABLED')    # Add double check for heater being off in state machine
    log.info('Warm System: Wait Until Warm: System warmed up')
