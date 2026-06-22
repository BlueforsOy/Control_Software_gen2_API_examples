"""API commands for the phase: PPC"""

import time
import logging

# params:
from functions import Timer, ErrorState, value, valves_on, valves_off, pump_on, pump_off, \
    heater_on, heater_off, set_heater_power, pulse_tube_on, pulse_tube_off, set_cold_cathode, \
    warmup_heater_1_on, warmup_heater_1_off, warmup_heater_2_on, warmup_heater_2_off, \
    circulation_turbo_pumps_on, circulation_turbo_pumps_off
from configuration import service_booster_pump_available

ppc_cycle_duration = 5400
ppc_pumping_time = 18
ppc_inlet_time = 8
ppc_pressure_limit_for_blocked_dr_unit = 0.05

timer = Timer()
log = logging.getLogger(__name__)


# PPC_Full #

def check_if_possible_state():
    # checks that ok to transition to this state
    if not value('PULSE_TUBE_ENABLED'):
        error = 'PPC ' + check_if_possible_state.__name__
        error_message = "Pulse tube is not running"
        log.error(error + ' msg:' + error_message)
        raise ErrorState(error, error_message)

    if value('P5_PRESSURE') < 0.550:
        error = 'PPC ' + check_if_possible_state.__name__
        error_message = "Helium tank pressure is low, check that mixture is in tank"
        log.error(error + ' msg:' + error_message)
        raise ErrorState(error, error_message)

    # Check that no part of the system is too warm for PPC cycle:
    if value('MXC_TEMPERATURE') > 80 or value('STILL_TEMPERATURE') > 15 or value('4K_TEMPERATURE') > 15 \
            or value('50K_TEMPERATURE') > 80:
        error = 'PPC ' + check_if_possible_state.__name__
        error_message = "System is too warm to run PPC"
        log.error(error + ' msg:' + error_message)
        raise ErrorState(error, error_message)
        # Specific temperature trigger to enter PPC:


def initial_settings():
    # initial settings for the state
    circulation_turbo_pumps_off('TURBO_PUMP')
    while value('B1A_SPEED') > 50:
        time.sleep(15)
        log.info('Waiting for turbo pump to spin down')


def close_critical_valves():
    # make sure critical valves and pumps are closed/turned off
    pump_off('R2') # turn off service_rough_pump
    valves_off(['V112', 'V113', 'V114', 'V203', 'V004', 'V003', 'V005', 'V303', 'V306', 'V403', 'V404', 'V406' 'V502H', 'V101', 'V104'])
    if service_booster_pump_available:
        pump_off('B2') # turn off service_booster_pump
        valves_off(['V106', 'V107'])
    else:
        valves_off(['V105'])


def evacuate_dr():
    log.info('PPC: Evacuate DR: Turn on circulation_rough_pump and valves')
    valves_on(['V202', 'V203', 'V502H', 'V504H', 'V001', 'V005', 'V302', 'V304'])
    pump_on('R1A') # turn on circulation_rough_pump
    time.sleep(10)

    while value('P3_PRESSURE') > 0.01:
        time.sleep(15)

    valves_off(['V502H', 'V001'])


def ppc_loop():
    log.info('PPC: PPC Loop: Entering the main PPC Cycle')
    timer.reset()
    valves_on(['V403'])

    while timer < ppc_cycle_duration:
        valves_off(['V001'])
        valves_on(['V203'])
        time.sleep(ppc_inlet_time)
        valves_off(['V203'])
        valves_on(['V001'])
        time.sleep(ppc_pumping_time)

    valves_off(['V203'])
    valves_off(['V403'])
    valves_on(['V001'])

    if value('P3_PRESSURE') < ppc_pressure_limit_for_blocked_dr_unit:
        error = 'PPC' + ppc_loop.__name__
        error_message = "Dilution unit blocked"
        log.error(error + ' msg:' + error_message)
        raise ErrorState(error, error_message)
    time.sleep(40)


def start_circulation():
    log.info('PPC: Start Circulation: Entering start_circulation()')
    log.info('PPC: Start Circulation: Small amount of mixture is left in circulation')
    valves_off(['V005'])
    valves_on(['V403'])
    time.sleep(2)
    valves_on(['V502H', 'V504H'])
    time.sleep(60)
    valves_on(['V201G'])
    valves_off(['V202'])
    time.sleep(60)


def ppc_finalize():
    log.info('PPC: PPC Finalize: Waiting until t_4K < 4.6, t_still < 5.3, and t_mix < 6:')
    while value('4K_TEMPERATURE') > 4.6 or value('STILL_TEMPERATURE') > 5.3 or value('MXC_TEMPERATURE') > 6:
        time.sleep(15)
    # Extra wait time before condensing
    time.sleep(600)
