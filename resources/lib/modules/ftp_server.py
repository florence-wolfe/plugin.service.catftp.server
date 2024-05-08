import os
import xbmc
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from modules.logger import log
from modules.constants import ADDON_NAME


def run_ftp_server(root_dir: str, port: int, username: str, password: str, secure: bool):
    server = None
    try:
        authorizer = DummyAuthorizer()
        authorizer.add_user(username, password, root_dir, perm="elradfmwMT")
        handler = FTPHandler
        handler.authorizer = authorizer
        handler.log_prefix = f"[{ADDON_NAME}][pyftpdlib]: [%(username)s]@%(remote_ip)s -"
        # TODO: Handle SSL in the future
        if secure:
            import ssl

            handler.tls_control_required = True
            handler.tls_data_required = True
            handler.certfile = os.path.join(root_dir, "server.crt")
            handler.keyfile = os.path.join(root_dir, "server.key")
        
            server = FTPServer(("0.0.0.0", port), handler)
        log(f"Starting {ADDON_NAME} on port {port}")
        server.serve_forever()
    except Exception as e:
        log(f"Error starting FTP server in run_ftp_server: {e}", level=xbmc.LOGERROR)
    finally:
        if server:
            server.close_all()