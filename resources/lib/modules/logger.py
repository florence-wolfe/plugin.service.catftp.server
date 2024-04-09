import xbmc
from modules.constants import ADDON_NAME


def log(message: str, level = xbmc.LOGINFO):
    xbmc.log(f"[{ADDON_NAME}]: {message}", level)
