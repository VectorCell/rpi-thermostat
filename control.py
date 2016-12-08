#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
import getpass
import time
import string


def printlog(*t, **d):
    print('[{}]'.format(time.strftime('%Y-%m-%d_%H:%M:%S')), end=' ')
    def str_to_bytearray(s):
        if not isinstance(s, str):
            return s
        for c in s:
            if c not in string.printable:
                return bytearray(s, 'utf-8')
        return s
    def reform_bytearray(ba):
        if not isinstance(ba, bytearray):
            return ba
        return str(ba)[len('bytearray('):][:-1]
    tcopy = tuple(reform_bytearray(str_to_bytearray(e)) for e in t)
    print(*tcopy, **d)


def get_sighandler():
	def sighandler(sig, frame):
		if sig == signal.SIGINT or sig == signal.SIGTERM:
			sys.exit(0)
	return sighandler


def run_command(cmd):
	if cmd.startswith('./'):
		cmd = os.path.dirname(os.path.realpath(__file__)) + cmd[1:]
	output = subprocess.getoutput(cmd)
	return output


def get_temp_c():
	user = getpass.getuser()
	temp = run_command('/home/{}/bin/dht11_c'.format(user))
	return int(temp)


class Heater:

	def __init__(self):
		self.state = False

	def update_relay(self, temp):
		state_str = 'off'
		if self.state:
			state_str = 'on'
		output = run_command('/home/{}/bin/relays {} {}'.format(
			getpass.getuser(),
			state_str,
			'ext'))
		if temp is not None:
			printlog('temp is {} C, heater {}'.format(temp, state_str))
		else:
			printlog('ERROR: temp info not provided')

	def set_state(self, state, temp):
		if self.state != state:
			self.state = state
			self.update_relay(temp)


	def off(self, temp = None):
		self.set_state(False, temp)

	def on(self, temp = None):
		self.set_state(True, temp)


def maintain_temp(goal, threshold = 2):
	heater = Heater()
	limit_low = goal - threshold
	limit_high = goal + threshold
	print('maintaining {} C ({} - {})'.format(goal,
	                                          limit_low,
	                                          limit_high))
	while True:
		temp = get_temp_c()
		printlog('temp is {} C'.format(temp))
		if temp <= limit_low:
			heater.on(temp)
		elif temp >= limit_high:
			heater.off(temp)
		time.sleep(30)



def main():
	signal.signal(signal.SIGINT, get_sighandler())
	signal.signal(signal.SIGTERM, get_sighandler())
	maintain_temp(23, 2)


if __name__ == '__main__':
	main()
