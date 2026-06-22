"""API commands for the phase: Pump VC"""

import time
import logging

# params:
from functions import Timer, ErrorState, value, valves_on, valves_off, pump_on, pump_off, \
    heater_on, heater_off, set_heater_power, pulse_tube_on, pulse_tube_off, set_cold_cathode, \
    warmup_heater_1_on, warmup_heater_1_off, warmup_heater_2_on, warmup_heater_2_off, \
    circulation_turbo_pumps_on, circulation_turbo_pumps_off
from configuration import service_booster_pump_available

# use bar for pressure

vc_dr_evacuated_pressure = 0.01 # in bar
vc_rough_pumping_max_time = 3600 # in seconds
vc_turbo_pumping_max_time = 7200 # in seconds
vc_pumping_rough_pumping_final_pressure = 1e-3 # in bar
vc_pumping_turbo_final_pressure = 5e-5 # in bar

timer = Timer()
log = logging.getLogger(__name__)


def check_if_possible_state():
    # check if p3 is evacuated
    if value('P3_PRESSURE') > vc_dr_evacuated_pressure:
        error = 'Pump VC ' + check_if_possible_state.__name__
        log.error(error)
        raise ErrorState(error)


def initial_settings():
    if not value('P1_ENABLED'):
        set_cold_cathode('plc.IO.P1')
        time.sleep(5)
        # double check that pressure gauge p1 cold cathode is active:
        if not value('P1_ENABLED'):
            error_message = "Pressure gauge p1 high vacuum measurement not enabled, please check"
            error = 'Pump VC ' + initial_settings.__name__
            log.error(error + ' msg:' + error_message)
            raise ErrorState(error, error_message)
    log.info('Pump VC: Initial Settings: P1 On')

def off_all():
    log.info('Pump VC: Off All: Turning off all valves and pumps')
    valves_off(['V201G', 'V202', 'V203', 'V502H', 'V501H', 'V503H', 'V401', 'V403', 'V402', \
                'V001', 'V004', 'V003', 'V005', 'V101', 'V112', 'V104', 'V113', 'V114', 'V110', \
                'V108', 'V105', 'V107', 'V106', 'V301', 'V302', 'V303', 'V304', 'V305', 'V306', \
                'V102', 'V109', 'V111', 'V404', 'V405', 'V406', 'V407'])
    circulation_turbo_pumps_off('TURBO_PUMP')
    for pump in ['R1A', 'B2', 'R2', 'COM']: # circulation_rough_pump, service_booster_pump, service_rough_pump, helium_compressor
        pump_off(pump)


def rough_pumping():
    # Pump VC with rough pump
    log.info('Pump VC: Rough Pumping: Starting Rough Pumping')
    off_all()
    time.sleep(2)
    pump_on('R2') # turn on service_rough_pump
    time.sleep(40)
    valves_on(['V105', 'V104', 'V101'])
    time.sleep(10)
    timer.reset()
    while value('P1_PRESSURE') > vc_pumping_rough_pumping_final_pressure:
        if timer > vc_rough_pumping_max_time:
            error = 'Pump VC ' + rough_pumping.__name__
            error_message = "PUMP_VC_ROUGH_PUMPING_MAX_TIME_OVER"
            log.error(error + ' msg:' + error_message)
            raise ErrorState(error, error_message)
    # now rough pumped VC below 1 mBar


def turbo_pumping():
    log.info('Pump VC: Turbo Pumping: Starting Turbo Pumping')
    if service_booster_pump_available:
        timer.reset()
        pump_on('B2') # turn on service_booster_pump
        valves_off(['V105'])
        valves_on(['V106', 'V107'])
        while value('P1_PRESSURE') > vc_pumping_turbo_final_pressure:
            if timer > vc_turbo_pumping_max_time:
                error = 'Pump VC ' + rough_pumping.__name__
                error_message = "PUMP_VC_TURBO_PUMPING_MAX_TIME_OVER"
                log.error(error + ' msg:' + error_message)
                raise ErrorState(error, error_message)
    else:
        valves_off(['V104'])
        valves_on(['V112', 'V114'])
        circulation_turbo_pumps_on('TURBO_PUMP')
        timer.reset()
        while value('P1_PRESSURE') > vc_pumping_turbo_final_pressure:
            if timer > vc_turbo_pumping_max_time:
                error = 'Pump VC ' + rough_pumping.__name__
                error_message = "PUMP_VC_TURBO_PUMPING_MAX_TIME_OVER"
                log.error(error + ' msg:' + error_message)
                raise ErrorState(error, error_message)
