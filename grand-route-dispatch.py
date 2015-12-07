#!/usr/bin/env python
# coding: utf-8

# Route dispatcher is a tool that dispatch specific
# websites or IPs to which device you want
# For example, Spotify will be redirected to Wi-Fi
# when your ldap server will be redirect to Ethernet


# TODO: [OSX] Check if Wi-Fi is upper Ethernet
# TODO: If default is Wi-Fi don't process Wi-Fi list
#       else if Ethernet is default don't process Ethernet list
# TODO: Add -a arg to process list without taking default device in account

import os
import re
from socket import gethostbyname_ex, gaierror
import platform
import argparse
import subprocess
from pprint import pprint

WIFI_GATEWAY = ""
ETHERNET_GATEWAY = ""
wifi_hosts = []
ethernet_hosts = []
default_file_name = "hostslist.txt"
WIFI_TAG = "!wifi"
ETHERNET_TAG = "!ethernet"
DEBUG = False
CMD_WIFI_OSX = "networksetup -listnetworkserviceorder | awk '/Wi-Fi/{print $5}'"
CMD_ETHERNET_OSX = "networksetup -listnetworkserviceorder | awk '/Thunderbolt Ethernet/{print $6}'"
CMD_WIFI_ETHERNET_LINUX = "ip link show | grep \"state UP\" | awk '{print $2}'"
CMD_NETSTAT_OSX = "netstat -rn | grep 'default' | awk '{print $2 \":\" $6}'"
CMD_NETSTAT_LINUX = "netstat -r | grep 'default' | awk '{print $2 \":\" $8}'"
CMD_ROUTE_OSX = 'sudo route -n add -net '
CMD_ROUTE_LINUX = 'sudo route add -net '
CMD_INTERFACE_TRANSLATOR_OSX = 'networksetup -listnetworkserviceorder | awk \'/en0/\' | cut -f2 -d":" | cut -f1 -d","\''
NETMASK_OSX = ' '
NETMASK_LINUX = ' netmask 255.255.255.255 gw '
PLATFORM = "UNDEFINED"
IP_CIDR_RE = re.compile(r"(?<!\d\.)(?<!\d)(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}(?!\d|(?:\.\d))")
supported_platforms_list = ["Darwin", "Linux"]
OSX = "Darwin"
LINUX = "Linux"

"""
    OS specific functions
"""


def get_name_devices():
    """
        Get name of Wi-Fi and Ethernet devices.

        :return wifi_name: wifi device name
        :return ethernet_name: ethernet device name
        :rtype: str

        :example:
        >>> print get_name_devices_osx()
        ('en0', 'en5')

        .. todo:: Implement error handling instead of just passing
    """
    global CMD_WIFI_OSX
    global CMD_ETHERNET_OSX
    global CMD_WIFI_ETHERNET_LINUX
    devices_list = []
    wifi_name = ""
    ethernet_name = ""

    # OS X part
    if PLATFORM == OSX:
        process = subprocess.Popen(CMD_WIFI_OSX,
                                   shell=True,
                                   stdout=subprocess.PIPE)
        process.wait()
        wifi_name, err = process.communicate()
        if err is None:
            pass

        process = subprocess.Popen(CMD_ETHERNET_OSX,
                                   shell=True,
                                   stdout=subprocess.PIPE)
        process.wait()
        ethernet_name, err = process.communicate()
        if err is None:
            pass
    # End of OS X part

    # Linux part
    if PLATFORM == LINUX:
        process = subprocess.Popen(CMD_WIFI_ETHERNET_LINUX,
                                   shell=True,
                                   stdout=subprocess.PIPE)
        process.wait()
        devices_name, err = process.communicate()
        if err is None:
            pass

        devices_list = devices_name.splitlines()

        for device in devices_list:
            if device.startswith("wl"):
                wifi_name = device
            elif device.startswith("eth"):
                ethernet_name = device
            else:
                print("Unknown device")
                exit(-1)
    # End of Linux part

    if wifi_name == "" or ethernet_name == "":
        print "wifi_name: " + wifi_name
        print "ethernet_name: " + ethernet_name
        print "Something went wrong!"
        exit(-1)

    # Remove last character as it's a ")" on OSX and ":" on linux
    # and remove the trailing "\n"
    wifi_name = wifi_name[:-2].strip()
    ethernet_name = ethernet_name[:-2].strip()

    return wifi_name, ethernet_name


def get_default_gateway():
    """
        Get default gateway IP for Wi-Fi and Ethernet.

        :return wifi: wifi gateway ip
        :return ethernet: ethernet gateway ip
        :rtype: str

        :example:
        >>> TODO!!!

        .. note:: May be rewrite the mess with lists
        .. todo:: Implement error handling instead of just passing
    """
    global DEBUG
    global CMD_NETSTAT_OSX
    global CMD_NETSTAT_LINUX
    list_of_gateways = []

    if PLATFORM == OSX:
        CMD = CMD_NETSTAT_OSX
    elif PLATFORM == LINUX:
        CMD = CMD_NETSTAT_LINUX

    process = subprocess.Popen(CMD,
                               shell=True,
                               stdout=subprocess.PIPE)
    process.wait()
    gateways, err = process.communicate()
    if err is None:
        pass
    list_of_gateways = gateways.splitlines()
    if len(list_of_gateways) != 2:
        print "Miss a device!"
        print "Be sure Wi-Fi and Ethernet are connected"
        exit(-1)

    wifi_name, ethernet_name = get_name_devices()
    if wifi_name in list_of_gateways[0]:
        wifi = list_of_gateways[0].split(":", 1)[0]
    elif wifi_name in list_of_gateways[1]:
        wifi = list_of_gateways[1].split(":", 1)[0]

    if ethernet_name in list_of_gateways[0]:
        ethernet = list_of_gateways[0].split(":", 1)[0]
    elif ethernet_name in list_of_gateways[1]:
        ethernet = list_of_gateways[1].split(":", 1)[0]

    if DEBUG:
        print "Wi-FI gateway address: " + wifi
        print "Ethernet gateway address: " + ethernet

    return wifi, ethernet


def add_route(hosts, gateway):
    """
        Resolve url to IP from list file then add route to OS.
        :param hosts: list of url
        :param gateway: gateway ip address

        .. warnings:: OSX SPECIFIC FUCNTION
        .. todo:: Implement error handling instead of just passing
    """
    global DEBUG
    # Redirect stdout to /dev/null
    fnull = open(os.devnull, 'w')
    if PLATFORM == OSX:
        CMD = CMD_ROUTE_OSX
        NETMASK = NETMASK_OSX
    elif PLATFORM == LINUX:
        CMD = CMD_ROUTE_LINUX
        NETMASK = NETMASK_LINUX
    for host in hosts:
        print "  " + host + ": ",
        try:
            if not re.match(IP_CIDR_RE, host):
                # is not a CIDR IP
                hip = gethostbyname_ex(host)
                print hip[2][0]
                cmd = CMD + hip[2][0] + NETMASK + gateway
            else:
                # is a CIDR IP
                print "CIDR address"
                cmd = CMD + host + NETMASK + gateway
            process = subprocess.Popen(cmd,
                                       shell=True,
                                       stdout=fnull,
                                       stderr=subprocess.PIPE)
            process.wait()
            gateways, err = process.communicate()
            if err is None:
                pass
            if DEBUG:
                print "    " + cmd
        except gaierror:
            print host + " is not a valid url, bypassing..."


def interface_name_to_human_readable_name(interface):
    pass

"""
    End of OS specific functions
"""


def file_iterator(fp, device):
    """
        Return line-by-line url for specific devices.
        :param fp: file desciptor
        :param device: device name
        :return: for wifi, wifi url and for ethernet, ethernet url
        :rtype: str

        .. note:: not satisfied, should better handle !tag
    """
    with open(fp, "r") as myfile:
        for line in myfile:
            if device in line:
                break
        for line in myfile:
            yield line.rstrip()


def is_comment(line):
    return line.startswith('#')


def create_lists(fp):
    """
        Append list only with url, let comments, tag and empty lines besides
        :param fp: file desciptor

        .. note:: not satisfied, should better handle !tag
    """
    for line in file_iterator(fp, WIFI_TAG):
        # Break if line look like a tag
        if line.startswith("!"):
            break
        # Continue if line is a comment
        if is_comment(line):
            continue
        # Continue if empty line
        if not line.strip():
            continue
        wifi_hosts.append(line)
    for line in file_iterator(fp, ETHERNET_TAG):
        # Break if line look like a tag
        if line.startswith("!"):
            break
        # Continue if line is a comment
        if is_comment(line):
            continue
        # Continue if empty line
        if not line.strip():
            continue
        ethernet_hosts.append(line)


def check_hosts_list(filename):
    """
        Check if filename, given as parameter, point to a real file.

        :param filename: name of the file which contain a list of url
        :return: filename if it exist
        :rtype: str

        .. note:: probably need a rework
    """
    if filename is not None:
        # User give a filename
        if os.path.isfile(filename):
            return filename
        else:
            print "File doesn't exist"
            exit(-1)
    elif os.path.isfile(default_file_name):
        # Using default hosts list filename
        return default_file_name
    else:
        print "Unable to find " + default_file_name + " in current directory"
        exit(-2)


def main():
    """
        Main function.
    """
    global DEBUG
    global PLATFORM
    parser = argparse.ArgumentParser(description='Grand Route Dispatch is a ' +
                                                 'python script for routing ' +
                                                 'specific url to ' +
                                                 'Wi-Fi or Ethernet.')
    parser.add_argument('-f',
                        '--hostsfile',
                        help='use given hosts file',)
    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='pretty print debug info',
                        default=False)
    arg = parser.parse_args()

    fp = check_hosts_list(arg.hostsfile)
    create_lists(fp)

    PLATFORM = platform.system()
    if PLATFORM not in supported_platforms_list:
        print PLATFORM + " is not yet supported"
        exit(0)

    if arg.debug is True:
        DEBUG = True

    if DEBUG:
        pprint(wifi_hosts)
        pprint(ethernet_hosts)

    WIFI_GATEWAY, ETHERNET_GATEWAY = get_default_gateway()
    if WIFI_GATEWAY == "" or ETHERNET_GATEWAY == "":
        print "Error Wi-Fi or Ethernet address is empty"
        exit(-1)
    print "WIFI"
    add_route(wifi_hosts, WIFI_GATEWAY)
    print "ETHERNET"
    add_route(ethernet_hosts, ETHERNET_GATEWAY)

    print
    print "DONE!"

if __name__ == '__main__':
    main()
