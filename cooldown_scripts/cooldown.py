"""Cool a cryostat through the CS2 API."""

import logging

from functions import ErrorState
import pump_vc_full
import pt_cooling
import ppc_full
import condensing
import warm_system


# This program runs the cooldown_scripts through the CS2 API, currently
# implemented are the phases: Pump VC, PT Cooling, PPC, Condensing, Collect
# Mixture, Warmup System #

# The runner functions for each phase are defined here rather than in their
# separate files for the reason that it will be simpler to try to run the
# cooldown_scripts from a specific point if all the functions are being called
# in the same script.


# pump vc #
def run_pump_vc():
    try:
        pump_vc_full.check_if_possible_state()
        pump_vc_full.initial_settings()
        pump_vc_full.rough_pumping()
        pump_vc_full.turbo_pumping()
    except ErrorState:
        raise


# pt cooling #
def run_pt_cooling():
    try:
        pt_cooling.check_if_possible_state()
        pt_cooling.pt_on()
        pt_cooling.stop_vc_pumping()
        pt_cooling.pt_cooling_finalize()
    except ErrorState:
        raise


# ppc #
def run_ppc():
    try:
        ppc_full.check_if_possible_state()
        ppc_full.initial_settings()
        ppc_full.close_critical_valves()
        ppc_full.evacuate_dr()
        ppc_full.ppc_loop()
        ppc_full.start_circulation()
        ppc_full.ppc_finalize()
    except ErrorState:
        raise


# condensing #
def run_condensing():
    try:
        condensing.check_if_possible_state()
        condensing.initial_settings()
        condensing.close_critical_valves()
        condensing.condensing_init()
        condensing.condensing_high_p5()
        condensing.condensing_low_p5()
        condensing.condensing_finalize()
    except ErrorState:
        raise


# warm system #
def run_warm_system():
    try:
        warm_system.check_if_possible_state()
        warm_system.initial_settings()
        warm_system.stop_cooling()
        warm_system.collect_mixture()
        warm_system.stop_pumping()
        warm_system.wait_until_warm()
    except ErrorState:
        raise


# The cooldown process is defined inside main() function. The following example
# does a full cooldown, starting from evacuation of vacuum chamber

# To perform warmup, comment out all phases except run_warm_system()
# For the warmup, system is assumed to be in circulation mode (base temperature)


def main():
    """Select the phases to run and which order to run them in."""
    # Adding a '#' before the phase prevents it from running.
    try:
        run_pump_vc()
        run_pt_cooling()
        run_ppc()
        run_condensing()
        # run_warm_system()
    except ErrorState as err:
        print(err)


if __name__ == "__main__":
    # set the connection to the CS2 API
    logging.basicConfig(level=logging.INFO)

    # run the cooldown phases' runner functions
    main()
