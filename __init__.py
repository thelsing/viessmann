#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import socket
import threading
import subprocess
import time

class vcex(Exception):
    pass

class Viessmann():

    _items = []

    def __init__(self, smarthome, cycle=60, host='127.0.0.1', port=3002):
        self._sh = smarthome
        self._cycle = cycle
        self.host = host
        self.port = port
        self.logger = logging.getLogger("")
        self._lock = threading.Lock()
        self.connected = False
        self._connection_attempts = 0
        self._connection_errorlog = 60
        smarthome.connections.monitor(self)
        
    def connect(self):
        self.logger.debug("viessmann: connect");
        self._lock.acquire()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5)
            self._sock.connect((self.host, self.port))
            #read prompt
            data = self._sock.recv(7)
            self.logger.debug("viessmann: connect data: {0}".format(data))
        except Exception as e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                self.logger.error("viessmann: could not connect to {0}:{1}: {2}".format(self.host, self.port, e))
                self._connection_attempts = self._connection_errorlog
            self._lock.release()
            return
        else:
            self.connected = True
            self.logger.info("viessmann: connected to {0}:{1}".format(self.host, self.port))
            self._connection_attempts = 0
            self._lock.release()
            self._command_cycle()
            
    def close(self):
        self.connected = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self._sock.close()
        except:
            pass
            
    def _request(self, cmd):
        
        if not self.connected:
            raise vcex("No connection to vcontrold.")
        self._lock.acquire()
        try:
            self._sock.sendall((cmd + "\n").encode())
        except Exception as e:
            self.close()
            self._lock.release()
            raise vcex("error sending request: {0}".format(e))
        
        data = b""
        while True:
            try:
                chunk = self._sock.recv(100)
                if chunk == b'vctrld>':
                    break
                data = chunk
            except socket.timeout:
                self.close()
                self._lock.release()
                raise vcex("error receiving data: timeout")
            except Exception as e:
                self.close()
                self._lock.release()
                raise vcex("error receiving data: {0}".format(e))
        self._lock.release()
        return data
        
    def run(self):
        self.alive = True
        self._sh.scheduler.add("viessmann-cmds", self._command_cycle, cycle=self._cycle, prio=5, offset=0)

    def _command_cycle(self):
        if not self.connected:
            self.logger.debug("viessmann: not connected")
            return
            
        start = time.time()
        for item in self._items:
            if not self.alive:
                break
            cmd = item.conf['vcontrold_cmd']
            output = self._request(cmd)
            
            valueString = output.decode().strip()
            self.logger.debug("viessmann: item type:{0}".format(item.type()))
            self.logger.debug("viessmann: executed {0} got {1}".format(cmd, valueString))
            if item.type() == 'num':
                fvalue = float(valueString)
                item(fvalue, 'viessmann')
            elif item.type() == 'bool':
                bvalue = (float(valueString) > 0)
                self.logger.debug("viessmann: set {0} t0 {1}".format(item, bvalue))
                item(bvalue, 'viessmann')
            else:
                item(valueString, 'viessmann')

        cycletime = time.time() - start
        self.logger.debug("viessmann: command cycle takes {0} seconds".format(cycletime))

    def stop(self):
        self.alive = False
        self.close()

    def parse_item(self, item):
        if not 'vcontrold_cmd' in item.conf:
            return
        self.logger.debug("viessmann: parse item: {0}".format(item))
        self._items.append(item)
        return self.update_item

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'plugin':
            self.logger.info("update item: {0}".format(item.id()))
