#-*- coding: utf-8 -*-

#    Copyright (C) 2012-2014 Daniel Vidal de la Rubia
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation version 2.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>

import os
import sys
import math
from IcmpSocket import *
from IcmpPacket import *


class IcmpApp(object):
    def __init__(self):
        self.socket = IcmpSocket()
        self._file = None

        self.window_size = 50
        self.fingerprint = '\x90\x86\x27\x73'

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self._file is not None and not self._file.closed:
            self._file.close()


class IcmpSender(IcmpApp):

    def __init__(self, file_to_send):
        super(IcmpSender, self).__init__()
        self.file_path = file_to_send
        self._file = open(file_to_send, 'r')

    def send(self, dst_addr):
        seq = 1

        window = {}
        last_sent_seq = 0
        last_removed_seq = 0
        max_seq = int(math.ceil(float(os.path.getsize(self.file_path)) / ICMP_PAYLOAD_SIZE)) + 2

        #print('max_seq: %d' % max_seq)

        while last_sent_seq < max_seq:
            if last_sent_seq <= max_seq:
                if len(window) < self.window_size:
                    #print('Send packet %d' % seq)
                    sys.stdout.write('\r%d / %d' % (seq, max_seq))
                    sys.stdout.flush()

                    if seq == 1:
                        data = str(max_seq)
                    elif seq == max_seq:
                        data = '\x00' * 8
                    else:
                        data = self._file.read(ICMP_PAYLOAD_SIZE)

                    if data:
                        packet = IcmpPacket(ECHO_REQUEST, seq_n=seq, payload=data, fingerprint=self.fingerprint)
                        window[seq] = packet
                        self.socket.sendto(packet, dst_addr)
                        last_sent_seq = seq
                        seq += 1

            try:
                icmp = self.socket.recv()
            except socket.timeout:
                continue

            if icmp.type_packet is ECHO_REPLY and icmp.payload == self.fingerprint:
                reply_seq = icmp.seq_n

                if reply_seq < last_sent_seq:
                    #print('Resend packet %d' % (reply_seq + 1))
                    packet = window[reply_seq + 1]
                    self.socket.sendto(packet, dst_addr)
                elif reply_seq == max_seq:
                    break

                for _seq in range(last_removed_seq + 1, reply_seq + 1):
                    if _seq in window:
                        del window[_seq]
                last_removed_seq = reply_seq

        print('\n\nFinished')


class IcmpReceiver(IcmpApp):
    
    def __init__(self, file_to_receive):
        super(IcmpReceiver, self).__init__()
        self._file = open(file_to_receive, 'w')

    def receive(self, dst_addr):

        window = {}
        last_received_seq = 0
        max_seq = 0
        fail_counter = 0
        reply_hit_divisor = self.window_size / 2
        while True:
            next_seq = last_received_seq + 1

            try:
                if next_seq in window:
                    icmp = window[next_seq]
                else:
                    icmp = self.socket.recv()
            except socket.timeout:
                if last_received_seq != 0:
                    packet = IcmpPacket(ECHO_REPLY, seq_n=last_received_seq, payload=self.fingerprint)
                    self.socket.sendto(packet, dst_addr)
                continue

            fingerprint = icmp.fingerprint
            #icmp.payload = icmp.payload[len(self.fingerprint):]
            if icmp.type_packet is ECHO_REQUEST and fingerprint == self.fingerprint:
                seq = icmp.seq_n

                if seq not in window and len(window) < self.window_size:
                    window[seq] = icmp

                if seq == next_seq:
                    #print('Receive packet %d' % seq)
                    sys.stdout.write('\r%d / %d' % (seq, max_seq))
                    sys.stdout.flush()

                    if seq == 1:
                        max_seq = int(icmp.payload)
                    elif seq != max_seq:
                        self._file.write(icmp.payload)

                    last_received_seq = seq

                    if seq in window:
                        del window[seq]

                    if int(seq % reply_hit_divisor) == 0 or seq == max_seq:
                        packet = IcmpPacket(ECHO_REPLY, seq_n=seq, payload=self.fingerprint)
                        self.socket.sendto(packet, dst_addr)

                    if seq == max_seq:
                        break
                else:
                    fail_counter += 1
                    if fail_counter >= reply_hit_divisor:
                        #print('Reply %d' % last_received_seq)
                        packet = IcmpPacket(ECHO_REPLY, seq_n=last_received_seq, payload=self.fingerprint)
                        self.socket.sendto(packet, dst_addr)
                        fail_counter = 0

        print('\n\nFinished')
