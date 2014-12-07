# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class JunocloudMe(XFSHoster):
    __name__    = "JunocloudMe"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:\w+\.)?junocloud\.me/\w{12}'

    __description__ = """Junocloud.me hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "junocloud.me"

    URL_REPLACEMENTS = [(r'//(www\.)?junocloud', "//dl3.junocloud")]

    SIZE_PATTERN = r'<p class="request_filesize">Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>'

    OFFLINE_PATTERN = r'>No such file with this filename<'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'


getInfo = create_getInfo(JunocloudMe)
