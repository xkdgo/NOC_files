# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# NEC.IPaso.get_mac_address_table
# ---------------------------------------------------------------------
# Copyright (C) 2007-2018 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------


from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetconfig import IGetConfig
# from noc.core.http.client import fetch_sync
import requests
import re


class Script(BaseScript):
    name = "NEC.IPaso.get_mac_string"
    interface = IGetConfig

    def execute(self, interface=None, vlan=None, mac=None):
        regline = r"fdb_data\":\s+\"(?P<intpath>\S+)\""
        regex = re.compile(regline)
        r = ''
        session_id = self.scripts.get_ipaso_login()
        if session_id:
            user_sess = (self.credentials.get("user"), session_id)
        else:
            self.logger.debug("Can't login")
            return r

        operation = 'GET_LCT05040400_09'
        payload = "CGI_ID={}&USER_NAME={}&SESSION_ID={}".format(
                    operation, *user_sess)
        path = "/cgi/lct.cgi"
        url = "http://%s/cgi/lct.cgi" % self.credentials.get("address")
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0",
            'Referer': url,
            'X-Requested-With': "XMLHttpRequest",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache",
            'Cookie': "LCT_POLLTIME=NONE"
            # 'Postman-Token': "83b902b8-43b5-4fe9-b642-a339fcf8ee66"
            }
        proxies = {"http": "", "https":""}
        self.logger.debug("payload is: %s" % payload)
        self.logger.debug("headers is: %s" % headers)
        # code, headers1, result = fetch_sync(url, method="POST", headers=headers, body=payload, proxies=proxies)
        result = requests.request("POST", url, data=payload, headers=headers, proxies=proxies)
        self.logger.debug("result is: %s" % result.text)
        if "cgi_status\":\t\"0" in result.text:
            match = regex.search(str(result.text))
            grp = match.group('intpath')
            self.logger.debug("match = %s" % match)
            if match:
                del headers['Content-Type']
                payload = {
                    "CGI_ID": (None, "GET_LCT05040400_10"),
                    "FILE_NAME": (None, "Entry_table.txt"),
                    "DATA": (None, "%s" % grp),
                    "USER_NAME": (None, "%s" % user_sess[0]),
                    "SESSION_ID": (None, "%s" % user_sess[1])
                    }
                self.logger.debug("checking fdb table %s %s" % (headers, payload))
                response = requests.request("POST", url, files=payload, headers=headers, proxies=proxies)
                mactable = response.text
                r = mactable
                self.logger.debug("catched mactable %s" % mactable)
            else:
                return r
        else:
            self.logger.debug("failed to collect fdb table by cgi_status")
            return r

        return r

