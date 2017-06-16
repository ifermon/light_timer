#!/usr/bin/env python

import sdnotify
from datetime import datetime
from datetime import timedelta
from pytz import timezone
import pigpio
import time

WDOG_INTERVAL=15

# Specify turn on / turn off times as an hour of the day
# So example, we turn on at 4am and turn off at 10pm
# Use 24 hour clock 
# Assume time in local timezone (EST)
TURN_ON = 3
TURN_OFF = 21

# This is the broadcom pin identifier
LIGHT_SIGNAL_PIN = 7

def tz():
    return timezone('US/Eastern')

def now():
    return datetime.now(tz())

def next_end_time():
    nw = now()
    if nw.hour >= TURN_OFF:
        # Need to increment the day
        tomorrow = nw + timedelta(days=1)
        ret_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, TURN_OFF, tzinfo=tz())
    else:
        ret_dt = datetime(nw.year, nw.month, nw.day, TURN_OFF, tzinfo=tz())
    return ret_dt

def next_start_time():
    nw = now()
    if nw.hour >= TURN_ON:
        # need to increment the day
        tomorrow = nw + timedelta(days=1)
        ret_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, TURN_ON, tzinfo=tz())
    else:
        ret_dt = datetime(nw.year, nw.month, nw.day, TURN_ON, tzinfo=tz())
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

    # We are a service, so set up notifications
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")

    print("TURN_ON = {}".format(TURN_ON))
    print("TURN_OFF = {}".format(TURN_OFF))

    while True:
        if now().hour < TURN_OFF and now().hour > TURN_ON:
            print("Turning on lights")
            print("now = {}".format(now()))
            print("next_end_time = {}".format(next_end_time()))
            print("next_start_time = {}".format(next_start_time()))
            turn_on_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_end_time() - now()).seconds
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")
        else:
            print("Turning off lights")
            turn_off_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_start_time() - now()).seconds
            print("Total sleep time = {}".format(total_sleep_time))
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")
