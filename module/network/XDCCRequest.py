#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: jeix
"""

import os
import select
import socket
import struct
import time

from module.plugins.Plugin import Abort


class XDCCRequest():
    def __init__(self, options={}):
        self.proxies = options.get('proxies', {})

        self.filesize = 0
        self.recv = 0
        self.speed = 0
        self.abort = False

    
    def createSocket(self):
        # proxytype = None
        # proxy = None
        # if self.proxies.has_key("socks5"):
            # proxytype = socks.PROXY_TYPE_SOCKS5
            # proxy = self.proxies["socks5"]
        # elif self.proxies.has_key("socks4"):
            # proxytype = socks.PROXY_TYPE_SOCKS4
            # proxy = self.proxies["socks4"]
        # if proxytype:
            # sock = socks.socksocket()
            # t = _parse_proxy(proxy)
            # sock.setproxy(proxytype, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        # else:
            # sock = socket.socket()
        # return sock

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)

        return sock
    
    def download(self, ip, port, filename, progressNotify=None, resume=None):
        chunck_name = filename + ".chunk0"
        if resume and os.path.exists(chunck_name):
            fh = open(chunck_name, "ab")
            resume_position = fh.tell()
            if not resume_position:
                resume_position = os.stat(chunck_name).st_size

            resume_position = resume(resume_position)
            fh.truncate(resume_position)
            self.recv = resume_position

        else:
            fh = open(chunck_name, "wb")

        lastUpdate = time.time()
        cumRecvLen = 0

        dccsock = self.createSocket()

        recv_list = [dccsock]
        dccsock.connect((ip, port))
        dccsock.setblocking(0)


        # recv loop for dcc socket
        while True:
            data = ""
            if self.abort:
                dccsock.close()
                fh.close()
                raise Abort()

            recv_socks,_,_ = select.select(recv_list, [], [],1)
            if self.recv == self.filesize:
                break
            elif dccsock in recv_socks:
                try:
                    while True:
                        t_data = dccsock.recv(1024)
                        data += t_data
                except Exception as ex:
                    if ex.errno == 11:  # EAGAIN
                        pass
                    else:
                        raise ex

                dataLen = len(data)
                self.recv += dataLen

                cumRecvLen += dataLen

                # write data to file
                fh.write(data)

                # acknowledge data received but this sometimes blocks forever
                # so we just ignore the error and continue as if nothing
                # happened
                # https://github.com/cinchrb/cinch/blob/master/lib/cinch/dcc/incoming/send.rb#L110
                try:
                    dccsock.send(struct.pack('!I', dataLen))
                    pass
                except Exception as ex:
                    if ex.errno == 11: pass
                    else: raise ex
            else: continue

            now = time.time()
            timespan = now - lastUpdate
            if timespan > 5:
                self.speed = cumRecvLen / timespan
                cumRecvLen = 0
                lastUpdate = now

                if progressNotify:
                    progressNotify(self.percent)

        dccsock.close()
        fh.close()
 
        os.rename(chunck_name, filename)

        return filename
    
    
    def abortDownloads(self):
        self.abort = True
    
    @property
    def size(self):
        return self.filesize

    @property
    def arrived(self):
        return self.recv

    @property
    def percent(self):
        if not self.filesize: return 0
        return (self.recv * 100) / self.filesize

    def close(self):
        pass
