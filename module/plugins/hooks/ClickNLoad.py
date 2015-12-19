# -*- coding: utf-8 -*-

import socket
import threading
import time

try:
    import ssl
except ImportError:
    pass

from module.plugins.internal.Addon import Addon, threaded


def forward(source, destination):
    try:
        bufsize = 1024
        bufdata = source.recv(bufsize)
        while bufdata:
            destination.sendall(bufdata)
            bufdata = source.recv(bufsize)
    finally:
        destination.shutdown(socket.SHUT_WR)


#@TODO: IPv6 support
class ClickNLoad(Addon):
    __name__    = "ClickNLoad"
    __type__    = "hook"
    __version__ = "0.50"
    __status__  = "testing"

    __config__ = [("activated", "bool"           , "Activated"                      , True       ),
                  ("port"     , "int"            , "Port"                           , 9666       ),
                  ("extern"   , "bool"           , "Listen for external connections", True       ),
                  ("dest"     , "queue;collector", "Add packages to"                , "collector")]

    __description__ = """Click'n'Load support"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.de"           ),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de"     , "nitzo2001[AT]yahoo[DOT]com")]


    def activate(self):
        if not self.pyload.config.get("webinterface", "activated"):
            return

        cnlip   = "" if self.get_config('extern') else "127.0.0.1"
        cnlport = self.get_config('port')
        webip   = self.pyload.config.get("webinterface", "host") or "127.0.0.1"
        webport = self.pyload.config.get("webinterface", "port")

        self.pyload.scheduler.addJob(5, self.proxy, [cnlip, cnlport, webip, webport], threaded=False)


    @threaded
    def forward(self, source, destination, queue=False):
        if queue:
            old_ids = set(pack.id for pack in self.pyload.api.getCollector())

        forward(source, destination)

        if queue:
            new_ids = set(pack.id for pack in self.pyload.api.getCollector())
            for id in new_ids - old_ids:
                self.pyload.api.pushToQueue(id)


    @threaded
    def proxy(self, cnlip, cnlport, webip, webport):
        self.log_info(_("Proxy listening on %s:%s") % (cnlip or "0.0.0.0", cnlport))

        self._server(cnlip, cnlport, webip, webport)

        lock = threading.Lock()
        lock.acquire()
        lock.acquire()


    @threaded
    def _server(self, cnlip, cnlport, webip, webport):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind((cnlip, cnlport))
            dock_socket.listen(5)

            while True:
                client_socket, client_addr = dock_socket.accept()
                self.log_debug("Connection from %s:%s" % client_addr)

                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                if self.pyload.config.get("webinterface", "https"):
                    try:
                        server_socket = ssl.wrap_socket(server_socket)

                    except NameError:
                        self.log_error(_("Missing SSL lib"), _("Please disable HTTPS in pyLoad settings"))
                        client_socket.close()
                        continue

                    except Exception, e:
                        self.log_error(_("SSL error: %s") % e.message)
                        client_socket.close()
                        continue

                server_socket.connect((webip, webport))

                self.forward(client_socket, server_socket, self.get_config('dest') is "queue")
                self.forward(server_socket, client_socket)

        except socket.timeout:
            self.log_debug("Connection timed out, retrying...")
            return self._server(cnlip, cnlport, webip, webport)

        except socket.error, e:
            self.log_error(e)
            time.sleep(240)
            return self._server(cnlip, cnlport, webip, webport)
