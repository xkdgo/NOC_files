# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# NEC.IPaso.get_mac_address_table
# ---------------------------------------------------------------------
# Copyright (C) 2007-2018 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------


from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetmacaddresstable import IGetMACAddressTable
# from noc.core.http.client import fetch_sync
import requests
import re
from pprint import pprint


class Script(BaseScript):
    name = "NEC.IPaso.get_mac_address_table"
    interface = IGetMACAddressTable

    def search_macs(self, mactable='', modems={}, slots={}):
        regs = r'^(?P<card>.*?)(?P<port>\d+)\s+(?P<mac>(?:\w{2}\:){5}\w{2})\s+(?P<vlan>\d+)\s+.*?$'
        regex = re.compile(regs, re.MULTILINE)
        catch = regex.finditer(mactable)
        for match in catch:
            card_from_mactable = match.group("card")
            if "GRP" in card_from_mactable:
                int_name = modems[match.group("port")]
            elif "SLOT" in card_from_mactable:
                slot = int(card_from_mactable.strip("SLOT"))
                port = int(match.group("port"))
                card = slots[card_from_mactable.rstrip()]
                int_name = card + "_Slot{}_Port0{}".format(
                                                slot,
                                                port)
            elif "main" in card_from_mactable.lower():
                port = int(match.group("port"))
                card = slots[card_from_mactable.rstrip()]
                int_name = card + "_Port0{}".format(port)
            else:
                pass
            mac = match.group("mac")
            vlan = match.group("vlan")
            yield (mac, int_name, vlan)

    def execute(self, interface=None, vlan=None, mac=None):

        r = []
        mactable = ''
        modems = {"100": "MODEM_1",
                  "101": "MODEM_3",
                  "102": "MODEM_5",
                  "103": "MODEM_7",
                  "104": "MODEM_9",
                  "105": "MODEM_11",
                  "106": "MODEM_13",
                  "01": "MODEM_1",
                  "02": "MODEM_3",
        }

        mactable = self.scripts.get_mac_string()
        slots = self.scripts.get_slots()
        vlanlst = self.scripts.get_vlans()
        vlans = []
        if vlanlst:
            for dct in vlanlst:
                vlans.append(int(dct["vlan_id"]))
        else:
            self.logger.debug("empty vlan table")
            pass

        if mactable:
            self.logger.debug("catched mactable %s" % mactable)
            for mac, ifname, vlan_id in self.search_macs(mactable=mactable , modems=modems, slots=slots):
                if int(vlan_id) in vlans:
                    r += [{
                    "vlan_id": vlan_id,
                    "mac": mac,
                    "interfaces": [ifname],
                    "type": "D"
                }]
                else:
                    continue
        else:
            self.logger.debug("could not catch mac table")
        self.logger.debug("platform is %s" % self.version.get("platform", "not_cathed"))
        return r

