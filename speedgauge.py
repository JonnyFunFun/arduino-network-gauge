#!/usr/bin/env python
'''
 *****************************************************************************
 * Arduino Network Gauge                                                     *
 *                                                                           *
 * Simple Arduino program to drive an automotive actuator ganked from an     *
 * HVAC system to be used as an internet utilization gauge.                  *
 *                                                                           *
 * By Jonathan "JonnyFunFun" Enzinna <www.jonathanenzinna.com>               *
 * This is free and unencumbered software released into the public domain.   *
 * For more information, please refer to the LIENSE file                     *
 *                                                                           *
 * For more information on the Arduino Network Gauge project, please visit:  *
 * <url_coming_soon>                                                         *
 *****************************************************************************
'''
from __future__ import division
from __future__ import print_function
from time import sleep
from sys import stdout, stderr
import argparse
import serial


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def read_bytes(interface):
    """
    Gather transferred/received bytes on interface
    :param interface: interface to poll
    :return: (tx_bytes, rx_bytes, )
    """
    with open("/sys/class/net/%s/statistics/tx_bytes" % interface, "r") as tx:
        tx_bytes = int(tx.read().__str__()) * 8  # byte -> bits
    with open("/sys/class/net/%s/statistics/rx_bytes" % interface, "r") as rx:
        rx_bytes = int(rx.read().__str__()) * 8  # byte -> bits
    return tx_bytes, rx_bytes


def polling_loop(interface, arduino, quiet, rate, pipe_size, use_arduino, arduino_post_tx):
    if pipe_size == 0:
        # pull the speed of our connection from the link
        with open("/sys/class/net/%s/speed" % interface, "r") as link_speed:
            pipe_size = int(link_speed.read().__str__())
    stdout.write("Starting up with interface %s (speed considered max: %dMBit)\n" % (interface, pipe_size))
    arduino_interface = None
    if use_arduino:
        stdout.write("Initializing Arduino interface on %s\n" % arduino)
        arduino_interface = serial.Serial(arduino, 9600)
        if not arduino_interface.isOpen():
            stderr.write("Unable to open Arduino interface on %d\n" % arduino)
            return
    last_tx, last_rx = read_bytes("eno1")
    while True:
        sleep(rate)
        new_tx, new_rx = read_bytes("eno1")
        speed_tx, speed_rx = (new_tx - last_tx) / rate, (new_rx - last_rx) / rate
        if not quiet:
            stdout.write('\rRx: %s/sec   Tx: %s/sec                 ' % (sizeof_fmt(speed_rx), sizeof_fmt(speed_tx)))
        if use_arduino:
            # send our info over to the Arduino
            bandwidth = speed_tx if arduino_post_tx else speed_rx
            bandwidth /= 1048576  # convert to megabits
            percentage_used = round((bandwidth / pipe_size) * 100)
            arduino_interface.write((str(percentage_used)+"\n").encode())
        last_tx, last_rx = new_tx, new_rx


def main():
    arg_parser = argparse.ArgumentParser(description="Network interface monitoring with uplink to"
                                                     " Arduino-controlled gauge.")
    arg_parser.add_argument('interface', type=str, help="interface to monitor (i.e. - eth0)")
    arg_parser.add_argument('arduino', nargs='?', default='/dev/ttyUSB0', help="serial port connected to the Arduino (defaults to /dev/ttyUSB0)")
    arg_parser.add_argument('-p', '--pipe-size', metavar="#MBit", default=0, type=int, help='pipe size (defaults to link speed)')
    arg_parser.add_argument('-r', '--rate', metavar="#", default=1, type=int, help='interface polling rate (default: 1)')
    arg_parser.add_argument('-tx', '--use-transmit', dest='arduino_post_tx', action='store_true', default=False,
                            help='use transmit (TX) data on Arduino (default: False)')
    arg_parser.add_argument('--no-arduino', dest='use_arduino', action='store_false', default=True,
                            help='disable Arduino interface (default: False)')
    arg_parser.add_argument('--quiet', dest='quiet', action='store_true', default=False,
                            help='suppress interface statistic output')
    arguments = arg_parser.parse_args()
    polling_loop(**vars(arguments))


if __name__ == "__main__":
    main()
