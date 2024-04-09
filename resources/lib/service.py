import xbmcvfs
import xbmc
from modules.logger import log
from modules.ftp_server import run_ftp_server
from modules.constants import ADDON_NAME as addon_name, addon


if __name__ == "__main__":
    monitor = xbmc.Monitor()

    # TODO: Move these
    ftp_root = xbmcvfs.translatePath("special://home/")
    ftp_port = addon.getSetting("ftp_port")
    ftp_username = addon.getSetting("ftp_username")
    ftp_password = addon.getSetting("ftp_password")
    ftp_secure = addon.getSettingBool("ftp_secure")

    server = run_ftp_server(ftp_root, int(ftp_port), ftp_username, ftp_password, ftp_secure)

    while not monitor.abortRequested():
        if monitor.waitForAbort(5):
            break
    log(f"Stopping {addon_name}")