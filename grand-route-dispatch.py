#!/usr/bin/env python
# coding: utf-8

# Route dispatcher is a tool that dispatch specific
# websites or IPs to which device you want
# For example, Spotify will be redirected to Wi-Fi
# when your ldap server will be redirect to Ethernet


# TODO: [OSX] Check if Wi-Fi is upper Ethernet
# TODO: [Linux] Everything similar as OSX

import os
from socket import gethostbyname_ex, gaierror, inet_ntoa
import struct
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
CMD_WIFI = "networksetup -listnetworkserviceorder | awk '/Wi-Fi/{print $5}'"
CMD_ETHERNET = "networksetup -listnetworkserviceorder | awk '/Thunderbolt Ethernet/{print $6}'"
CMD_NETSTAT = "netstat -rn | grep 'default' | awk '{print $2 \":\" $6}'"


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


def get_default_gateway_linux():
    """
        Read the default gateway directly from /proc.

        :return:
        :rtype:

        .. note:: I don't have a big-endian machine to test on, so I'm not sure
                  whether the endianness is dependent on your processor
                  architecture, but if it is,
                  replace the < in struct.pack('<L', ... with = so the code
                  will use the machine's native endianness.
        .. warnings:: UNTESTED
        .. warnings:: LINUX SPECIFIC FUCNTION
        .. todo:: Fill return and rtype in comment
    """
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def get_name_devices_osx():
    """
        Get name of Wi-Fi and Ethernet devices.

        :return wifi_name: wifi device name
        :return ethernet_name: ethernet device name
        :rtype: str

        :example:
        >>> print get_name_devices_osx()
        ('en0', 'en5')

        .. warnings:: OSX SPECIFIC FUCNTION
        .. todo:: Implement error handling instead of just passing
    """
    global CMD_WIFI
    global CMD_ETHERNET

    process = subprocess.Popen(CMD_WIFI,
                               shell=True,
                               stdout=subprocess.PIPE)
    process.wait()
    wifi_name, err = process.communicate()
    if err is None:
        pass

    process = subprocess.Popen(CMD_ETHERNET,
                               shell=True,
                               stdout=subprocess.PIPE)
    process.wait()
    ethernet_name, err = process.communicate()
    if err is None:
        pass

    # Remove last character as it's a ")" and the trailing "\n"
    wifi_name = wifi_name[:-2].strip()
    ethernet_name = ethernet_name[:-2].strip()

    return wifi_name, ethernet_name


def get_default_gateway_osx():
    """
        Get default gateway IP for Wi-Fi and Ethernet.

        :return wifi: wifi gateway ip
        :return ethernet: ethernet gateway ip
        :rtype: str

        :example:
        >>> TODO!!!

        .. note:: May be rewrite the mess with lists
        .. warnings:: OSX SPECIFIC FUCNTION
        .. todo:: Implement error handling instead of just passing
    """
    global DEBUG
    global CMD_NETSTAT
    list_of_gateways = []

    process = subprocess.Popen(CMD_NETSTAT, shell=True, stdout=subprocess.PIPE)
    process.wait()
    gateways, err = process.communicate()
    if err is None:
        pass
    list_of_gateways = gateways.splitlines()
    if len(list_of_gateways) != 2:
        print "Miss a device!"
        print "Be sure Wi-Fi and Ethernet are connected"
        exit(-1)

    wifi_name, ethernet_name = get_name_devices_osx()
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


def add_route_osx(hosts, gateway):
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
    for host in hosts:
        print "  " + host + ": ",
        try:
            hip = gethostbyname_ex(host)
        except gaierror:
            print host + " is not a valid url, bypassing..."
        print hip[2][0]
        cmd = 'sudo route -n add -net ' + hip[2][0] + ' ' + gateway
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


def start_depending_platform():
    """
        Dispatch core functions depending on platform.
    """
    global DEBUG
    global WIFI_GATEWAY
    global ETHERNET_GATEWAY
    if platform.system() == "Darwin":
        WIFI_GATEWAY, ETHERNET_GATEWAY = get_default_gateway_osx()
        if WIFI_GATEWAY == "" or ETHERNET_GATEWAY == "":
            print "Error Wi-Fi or Ethernet address is empty"
            exit(-1)
        print "WIFI"
        add_route_osx(wifi_hosts, WIFI_GATEWAY)
        print "ETHERNET"
        add_route_osx(ethernet_hosts, ETHERNET_GATEWAY)

    elif platform.system() == "Linux":
        print "Not yet supported"
        exit(0)
    else:
        print "Unsupported OS"
        exit(0)


def main():
    """
        Main function.
    """
    global DEBUG
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

    if arg.debug is True:
        DEBUG = True

    if DEBUG:
        pprint(wifi_hosts)
        pprint(ethernet_hosts)

    start_depending_platform()

    print
    print "DONE!"

if __name__ == '__main__':
    main()
