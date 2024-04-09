import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo("name")
ADDON_PATH = xbmcvfs.translatePath(addon.getAddonInfo("path"))
