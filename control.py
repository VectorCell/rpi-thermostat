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


class Sensor:

	def __init__(self, cmd, filterfn = None, typecast = int):
		self.cmd = cmd
		self.filterfn = filterfn
		self.typecast = typecast

	def poll(self):
		val = run_command(self.cmd)
		if self.filterfn:
			val = self.filterfn(val)
		if isinstance(val, self.typecast):
			return val
		else:
			return self.typecast(val)


class BangBangPolicy:

	def __init__(self, limit_low, limit_high):
		self.limit_low = limit_low
		self.limit_high = limit_high

	def should_turn_on(self, temp):
		return temp <= self.limit_low

	def should_turn_off(self, temp):
		return temp >= self.limit_high

	def __repr__(self):
		return 'BangBangPolicy [{}-{}]'.format(
			self.limit_low,
			self.limit_high)


class Relay:

	def __init__(self, name):
		self.name = name
		self.user = getpass.getuser()

	def toggle(self):
		run_command('/home/{}/bin/relays toggle {}'.format(self.user, self.name))

	def on(self):
		run_command('/home/{}/bin/relays on {}'.format(self.user, self.name))

	def off(self):
		run_command('/home/{}/bin/relays off {}'.format(self.user, self.name))

	def state(self):
		return '1' == run_command('/home/{}/bin/relays state {}'.format(self.user, self.name))

	def set_state(self, state):
		if state:
			self.on()
		else:
			self.off()


class Heater:

	def __init__(self, tempsensor, policy, relayname):
		self.tempsensor = tempsensor
		self.policy = policy
		self.relay = Relay(relayname)
		self.running = False
		self.state = self.relay.state()

		printlog('created heater')
		printlog('policy', self.policy)
		printlog('starting temperature: {} C'.format(self.tempsensor.poll()))
		statename = 'OFF'
		if self.state:
			statename = 'ON'
		printlog('initialized with heater {}'.format(statename))

	def set_state(self, state, temp):
		if state != self.state:
			self.relay.set_state(state)
			self.state = state
			if state:
				printlog('temp is {} C, heater ON'.format(temp))
			else:
				printlog('temp is {} C, heater OFF'.format(temp))

	def start(self):
		self.running = True
		while self.running:
			temp = self.tempsensor.poll()
			if self.policy.should_turn_on(temp):
				self.set_state(True, temp)
			elif self.policy.should_turn_off(temp):
				self.set_state(False, temp)
			time.sleep(30)
	
	def stop(self):
		self.running = False



def maintain_temp(limit_low, limit_high):

	user = getpass.getuser()
	relayname = 'ext'

	tempsensor = Sensor('/home/{}/bin/dht11_c'.format(user))
	policy = BangBangPolicy(limit_low, limit_high)
	heater = Heater(tempsensor, policy, relayname)

	heater.start()



def main():
	signal.signal(signal.SIGINT, get_sighandler())
	signal.signal(signal.SIGTERM, get_sighandler())

	limit_low = 25
	limit_high = 27
	if len(sys.argv) > 1:
		goal = int(sys.argv[1])
	if len(sys.argv) > 2:
		threshold = int(sys.argv[2])
	maintain_temp(limit_low, limit_high)


if __name__ == '__main__':
	main()
