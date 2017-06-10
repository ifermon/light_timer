#!/usr/bin/env python

import sdnotify
from datetime import datetime
from pytz import timezone
import pigpio
import time

WDOG_INTERVAL=15

# Specify turn on / turn off times as an hour of the day
# So example, we turn on at 4am and turn off at 10pm
# Use 24 hour clock 
# Assume time in local timezone (EST)
TURN_ON = 4
TURN_OFF = 22

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
        tomorrow = nw + datetime.timedelta(days=1)
        ret_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, TURN_OFF, tzinfo=tz())
    else:
        ret_dt = datetime(nw.year, nw.month, nw.day, TURN_OFF, tzinfo=tz())
    return ret_dt

def next_start_time():
    nw = now()
    if nw.hour < TURN_ON:
        # need to increment the day
        tomorrow = nw + datetime.timedelta(days=1)
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

    while True:
        if now() < next_end_time() and now() > next_start_time():
            turn_on_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_end_time() - now()).seconds
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")
        else:
            turn_off_lights()

            # Wake up every few secs to tell systemd we are alive
            total_sleep_time = (next_start_time() - now()).seconds
            for intervals in range(int(total_sleep_time/WDOG_INTERVAL)):
                time.sleep(WDOG_INTERVAL)
                n.notify("WATCHDOG=1")

