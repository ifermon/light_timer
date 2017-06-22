#!/usr/bin/env python

import sdnotify
from datetime import datetime
from datetime import timedelta
from pytz import timezone
import pigpio
import time
import sys
import argparse

WDOG_INTERVAL=15

# Specify turn on / turn off times as an hour of the day
# So example, we turn on at 4am and turn off at 10pm
# Use 24 hour clock 
# Assume time in local timezone (EST)
TURN_ON = 3
TURN_OFF = 21

# This is the broadcom pin identifier
LIGHT_SIGNAL_PIN = 7

def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("-off", action="store_true", help="Turn off light")
    parser.add_argument("-on", action="store_true", help="Turn on light")
    parser.add_argument("-debug", action="store_true", help="Print converted times")
    return parser.parse_args()

def tz():
    return timezone('US/Eastern')

def now():
    return datetime.now(tz())

def next_end_time():
    nw = now()
    if nw.hour >= TURN_OFF:
        # Need to increment the day
        tomorrow = nw + timedelta(days=1)
        ret_dt = tz().localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day, TURN_OFF))
    else:
        ret_dt = tz().localize(datetime(nw.year, nw.month, nw.day, TURN_OFF))
    return ret_dt

def next_start_time():
    nw = now()
    if nw.hour >= TURN_ON:
        # need to increment the day
        tomorrow = nw + timedelta(days=1)
        ret_dt = tz().localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day, TURN_ON))
    else:
        ret_dt = tz().localize(datetime(nw.year, nw.month, nw.day, TURN_ON))
    return ret_dt

def turn_on_lights():
    global pi
    print("Turning on")
    pi.write(LIGHT_SIGNAL_PIN, 1)
    pass

def turn_off_lights():
    global pi
    print("Turning off")
    pi.write(LIGHT_SIGNAL_PIN, 0)
    pass

def configure_gpio():
    pi = pigpio.pi()
    pi.set_mode(LIGHT_SIGNAL_PIN, pigpio.OUTPUT)
    return pi

if __name__ == "__main__":

    pi = configure_gpio()

    args = parse_command_line()

    if args.on:
        print("Turning on lights and exitting")
        turn_on_lights()
        sys.exit()

    if args.off:
        print("Turning off lights and exitting")
        turn_off_lights()
        sys.exit()

    if args.debug:
        print("next_end_time {}".format(next_end_time()))
        print("next_start_time {}".format(next_start_time()))
        print("now {}".format(now()))
        sys.exit()

    # We are a service, so set up notifications
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")

    print("TURN_ON = {}".format(TURN_ON))
    print("TURN_OFF = {}".format(TURN_OFF))

    while True:
        if now().hour < TURN_OFF and now().hour >= TURN_ON:
            print("Turning on lights")
            print("now = {}".format(now()))
            print("next_end_time = {}".format(next_end_time()))
            print("next_start_time = {}".format(next_start_time()))
            turn_on_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_end_time() - now()).total_seconds()
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")
        else:
            print("Turning off lights")
            turn_off_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_start_time() - now()).seconds
            print("Total sleep time = {}".format(total_sleep_time))
            print("next start time {}".format(next_start_time()))
            print("now {}".format(now()))
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")

