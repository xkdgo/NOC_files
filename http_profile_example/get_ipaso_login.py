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
    name = "NEC.IPaso.get_ipaso_login"
    interface = IGetConfig

    def execute(self):
        sessionline = r"^<.*?id=LCTSESSIONID.*?value=\'(?P<sessionid>\d+)\'>$"
        sessionline_regex = re.compile(sessionline, re.MULTILINE)
        r = ""
        #GET_LCT01000000_01
        payload = "CGI_ID=GET_LCT01000000_01&userName={}&password={}".format(
            self.credentials.get("user"),
            self.credentials.get("password"),
        )
        path = "/cgi/lct.cgi"
        url = "http://%s/cgi/lct.cgi" % self.credentials.get("address")
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0",
            'Cache-Control': "no-cache",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cookie': "LCT_POLLTIME=NONE"
        }
        proxies = {"http": "", "https":""}
        dhp = dict(data=payload, headers=headers, proxies=proxies)
        self.logger.debug("payload is: %s" % payload)
        self.logger.debug("headers is: %s" % headers)

        response = requests.request("POST", url, **dhp)

        self.logger.debug("response is: %s" % response.text)

        match = sessionline_regex.search(response.text)
        if match:
            session_id = match.group("sessionid")
            self.logger.debug("find session_id: %s" % session_id)
        else:
            self.logger.debug("cant find session id")
            return ""

        #GET_LCT01000000_02
        #new payload
        user_sess = (self.credentials.get("user"), session_id)
        operation = 'GET_LCT01000000_02'
        payload = "CGI_ID={}&USER_NAME={}&SESSION_ID={}".format(operation, *user_sess)
        #new key in headers
        headers['Referer'] = url
        dhp['data']=payload
        dhp['headers']=headers
        response = requests.request("POST", url, **dhp)
        self.logger.debug("response GET_LCT01000000_02 %s" % response.text)
        if "cgi_status\":\t\"0" in response.text:
            # if success GET_LCT01000000_03
            self.logger.debug("operation OK %s" % operation)
            operation = 'GET_LCT01000000_03'
            payload = "CGI_ID={}&userName={}&SESSION_ID={}".format(operation, *user_sess)
            dhp['data']=payload
            response = requests.request("POST", url, **dhp)
            self.logger.debug("response GET_LCT01000000_03 %s" % response.text)
            if not "doLogin\":\t\"1":
                self.logger.debug("unseccessful operation %s" % operation)
                return ""
            else:
                pass
        else:
            self.logger.debug("unseccessful operation %s" % operation)
            return ""

        r = session_id
        return r

