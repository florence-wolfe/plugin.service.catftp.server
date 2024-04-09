# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"""
This module contains the main FTPServer class which listens on a
host:port and dispatches the incoming connections to a handler.
The concurrency is handled asynchronously by the main process thread,
meaning the handler cannot block otherwise the whole server will hang.

Other than that we have 2 subclasses changing the asynchronous concurrency
model using multiple threads or processes.

You might be interested in these in case your code contains blocking
parts which cannot be adapted to the base async model or if the
underlying filesystem is particularly slow, see:

https://github.com/giampaolo/pyftpdlib/issues/197
https://github.com/giampaolo/pyftpdlib/issues/212

Two classes are provided:

 - ThreadingFTPServer
 - MultiprocessFTPServer

...spawning a new thread or process every time a client connects.

The main thread will be async-based and be used only to accept new
connections.
Every time a new connection comes in that will be dispatched to a
separate thread/process which internally will run its own IO loop.
This way the handler handling that connections will be free to block
without hanging the whole FTP server.
"""
import os
import traceback

from .ioloop import Acceptor
from .log import PREFIX
from .log import PREFIX_MPROC
from .log import config_logging
from .log import is_logging_configured
from .log import logger
from .prefork import fork_processes

__all__ = ['FTPServer']


# ===================================================================
# --- base class
# ===================================================================


class FTPServer(Acceptor):
    """Creates a socket listening on <address>, dispatching the requests
    to a <handler> (typically FTPHandler class).

    Depending on the type of address specified IPv4 or IPv6 connections
    (or both, depending from the underlying system) will be accepted.

    All relevant session information is stored in class attributes
    described below.

     - (int) max_cons:
        number of maximum simultaneous connections accepted (defaults
        to 512). Can be set to 0 for unlimited but it is recommended
        to always have a limit to avoid running out of file descriptors
        (DoS).

     - (int) max_cons_per_ip:
        number of maximum connections accepted for the same IP address
        (defaults to 0 == unlimited).
    """

    max_cons = 512
    max_cons_per_ip = 0

    def __init__(self, address_or_socket, handler, ioloop=None, backlog=100):
        """Creates a socket listening on 'address' dispatching
        connections to a 'handler'.

         - (tuple) address_or_socket: the (host, port) pair on which
           the command channel will listen for incoming connections or
           an existent socket object.

         - (instance) handler: the handler class to use.

         - (instance) ioloop: a pyftpdlib.ioloop.IOLoop instance

         - (int) backlog: the maximum number of queued connections
           passed to listen(). If a connection request arrives when
           the queue is full the client may raise ECONNRESET.
           Defaults to 5.
        """
        Acceptor.__init__(self, ioloop=ioloop)
        self.handler = handler
        self.backlog = backlog
        self.ip_map = []
        # in case of FTPS class not properly configured we want errors
        # to be raised here rather than later, when client connects
        if hasattr(handler, 'get_ssl_context'):
            handler.get_ssl_context()
        if callable(getattr(address_or_socket, 'listen', None)):
            sock = address_or_socket
            sock.setblocking(0)
            self.set_socket(sock)
        else:
            self.bind_af_unspecified(address_or_socket)
        self.listen(backlog)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_all()

    @property
    def address(self):
        """The address this server is listening on as a (ip, port) tuple."""
        return self.socket.getsockname()[:2]

    def _map_len(self):
        return len(self.ioloop.socket_map)

    def _accept_new_cons(self):
        """Return True if the server is willing to accept new connections."""
        if not self.max_cons:
            return True
        else:
            return self._map_len() <= self.max_cons

    def _log_start(self, prefork=False):
        def get_fqname(obj):
            try:
                return obj.__module__ + "." + obj.__class__.__name__
            except AttributeError:
                try:
                    return obj.__module__ + "." + obj.__name__
                except AttributeError:
                    return str(obj)

        if not is_logging_configured():
            # If we get to this point it means the user hasn't
            # configured any logger. We want logging to be on
            # by default (stderr).
            config_logging(prefix=PREFIX_MPROC if prefork else PREFIX)

        if self.handler.passive_ports:
            pasv_ports = "%s->%s" % (
                self.handler.passive_ports[0],
                self.handler.passive_ports[-1],
            )
        else:
            pasv_ports = None
        model = 'prefork + ' if prefork else ''
        if 'MultiprocessFTPServer' in __all__ and issubclass(
            self.__class__, MultiprocessFTPServer
        ):
            model += 'multi-process'
        elif issubclass(self.__class__, FTPServer):
            model += 'async'
        else:
            model += 'unknown (custom class)'
        logger.info("concurrency model: " + model)
        logger.info(
            "masquerade (NAT) address: %s", self.handler.masquerade_address
        )
        logger.info("passive ports: %s", pasv_ports)
        logger.debug("poller: %r", get_fqname(self.ioloop))
        logger.debug("authorizer: %r", get_fqname(self.handler.authorizer))
        if os.name == 'posix':
            logger.debug("use sendfile(2): %s", self.handler.use_sendfile)
        logger.debug("handler: %r", get_fqname(self.handler))
        logger.debug("max connections: %s", self.max_cons or "unlimited")
        logger.debug(
            "max connections per ip: %s", self.max_cons_per_ip or "unlimited"
        )
        logger.debug("timeout: %s", self.handler.timeout or "unlimited")
        logger.debug("banner: %r", self.handler.banner)
        logger.debug("max login attempts: %r", self.handler.max_login_attempts)
        if getattr(self.handler, 'certfile', None):
            logger.debug("SSL certfile: %r", self.handler.certfile)
        if getattr(self.handler, 'keyfile', None):
            logger.debug("SSL keyfile: %r", self.handler.keyfile)

    def serve_forever(
        self, timeout=None, blocking=True, handle_exit=True, worker_processes=1
    ):
        """Start serving.

        - (float) timeout: the timeout passed to the underlying IO
          loop expressed in seconds.

        - (bool) blocking: if False loop once and then return the
          timeout of the next scheduled call next to expire soonest
          (if any).

        - (bool) handle_exit: when True catches KeyboardInterrupt and
          SystemExit exceptions (generally caused by SIGTERM / SIGINT
          signals) and gracefully exits after cleaning up resources.
          Also, logs server start and stop.

        - (int) worker_processes: pre-fork a certain number of child
          processes before starting.
          Each child process will keep using a 1-thread, async
          concurrency model, handling multiple concurrent connections.
          If the number is None or <= 0 the number of usable cores
          available on this machine is detected and used.
          It is a good idea to use this option in case the app risks
          blocking for too long on a single function call (e.g.
          hard-disk is slow, long DB query on auth etc.).
          By splitting the work load over multiple processes the delay
          introduced by a blocking function call is amortized and divided
          by the number of worker processes.
        """
        log = handle_exit and blocking

        #
        if worker_processes != 1 and os.name == 'posix':
            if not blocking:
                raise ValueError(
                    "'worker_processes' and 'blocking' are mutually exclusive"
                )
            if log:
                self._log_start(prefork=True)
            fork_processes(worker_processes)
        else:
            if log:
                self._log_start()

        #
        proto = "FTP+SSL" if hasattr(self.handler, 'ssl_protocol') else "FTP"
        logger.info(
            ">>> starting %s server on %s:%s, pid=%i <<<"
            % (proto, self.address[0], self.address[1], os.getpid())
        )

        #
        if handle_exit:
            try:
                self.ioloop.loop(timeout, blocking)
            except (KeyboardInterrupt, SystemExit):
                logger.info("received interrupt signal")
            if blocking:
                if log:
                    logger.info(
                        ">>> shutting down FTP server, %s socket(s), pid=%i "
                        "<<<",
                        self._map_len(),
                        os.getpid(),
                    )
                self.close_all()
        else:
            self.ioloop.loop(timeout, blocking)

    def handle_accepted(self, sock, addr):
        """Called when remote client initiates a connection."""
        handler = None
        ip = None
        try:
            handler = self.handler(sock, self, ioloop=self.ioloop)
            if not handler.connected:
                return

            ip = addr[0]
            self.ip_map.append(ip)

            # For performance and security reasons we should always set a
            # limit for the number of file descriptors that socket_map
            # should contain.  When we're running out of such limit we'll
            # use the last available channel for sending a 421 response
            # to the client before disconnecting it.
            if not self._accept_new_cons():
                handler.handle_max_cons()
                return

            # accept only a limited number of connections from the same
            # source address.
            if self.max_cons_per_ip:
                if self.ip_map.count(ip) > self.max_cons_per_ip:
                    handler.handle_max_cons_per_ip()
                    return

            try:
                handler.handle()
            except Exception:
                handler.handle_error()
            else:
                return handler
        except Exception:
            # This is supposed to be an application bug that should
            # be fixed. We do not want to tear down the server though
            # (DoS). We just log the exception, hoping that someone
            # will eventually file a bug. References:
            # - https://github.com/giampaolo/pyftpdlib/issues/143
            # - https://github.com/giampaolo/pyftpdlib/issues/166
            # - https://groups.google.com/forum/#!topic/pyftpdlib/h7pPybzAx14
            logger.error(traceback.format_exc())
            if handler is not None:
                handler.close()
            else:
                if ip is not None and ip in self.ip_map:
                    self.ip_map.remove(ip)

    def handle_error(self):
        """Called to handle any uncaught exceptions."""
        try:
            raise  # noqa: PLE0704
        except Exception:
            logger.error(traceback.format_exc())
        self.close()

    def close_all(self):
        """Stop serving and also disconnects all currently connected
        clients.
        """
        return self.ioloop.close()
