#!/usr/bin/env python3

from LANforge.lfcli_base import LFCliBase
from LANforge import LFRequest
from LANforge import add_vap
from LANforge import set_port
from LANforge import LFUtils
import pprint
from pprint import pprint
import time


class VAPProfile(LFCliBase):
    def __init__(self, lfclient_host, lfclient_port, local_realm,
                 vap_name="",
                 ssid="NA",
                 ssid_pass="NA",
                 mode=0,
                 debug_=False):
        super().__init__(_lfjson_host=lfclient_host, _lfjson_port=lfclient_port, _debug=debug_)
        self.debug = debug_
        # self.lfclient_url = lfclient_url # done in super()
        self.ssid = ssid
        self.ssid_pass = ssid_pass
        self.mode = mode
        self.local_realm = local_realm
        self.vap_name = vap_name
        self.COMMANDS = ["add_vap", "set_port"]
        self.desired_add_vap_flags = ["wpa2_enable", "80211u_enable", "create_admin_down"]
        self.desired_add_vap_flags_mask = ["wpa2_enable", "80211u_enable", "create_admin_down"]

        self.add_vap_data = {
            "shelf": 1,
            "resource": 1,
            "radio": None,
            "ap_name": None,
            "flags": 0,
            "flags_mask": 0,
            "mode": 0,
            "ssid": None,
            "key": None,
            "mac": "xx:xx:xx:xx:*:xx"
        }

        self.desired_set_port_cmd_flags = []
        self.desired_set_port_current_flags = ["if_down"]
        self.desired_set_port_interest_flags = ["current_flags", "ifdown"]
        self.set_port_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "current_flags": 0,
            "interest": 0,  # (0x2 + 0x4000 + 0x800000)  # current, dhcp, down
        }
        self.wifi_extra_data_modified = False
        self.wifi_extra_data = {
            "shelf": 1,
            "resource": 1,
            "port": None,
            "key_mgmt": None,
            "eap": None,
            "hessid": None,
            "identity": None,
            "password": None,
            "realm": None,
            "domain": None
        }

    def set_wifi_extra(self,
                       key_mgmt="WPA-EAP",
                       pairwise="DEFAULT",
                       group="DEFAULT",
                       psk="[BLANK]",
                       eap="TTLS",
                       identity="testuser",
                       passwd="testpasswd",
                       realm="localhost.localdomain",
                       domain="localhost.localdomain",
                       hessid="00:00:00:00:00:01"):
        self.wifi_extra_data_modified = True
        self.wifi_extra_data["key_mgmt"] = key_mgmt
        self.wifi_extra_data["eap"] = eap
        self.wifi_extra_data["identity"] = identity
        self.wifi_extra_data["password"] = passwd
        self.wifi_extra_data["realm"] = realm
        self.wifi_extra_data["domain"] = domain
        self.wifi_extra_data["hessid"] = hessid

    def admin_up(self, resource):
        set_port_r = LFRequest.LFRequest(self.lfclient_url, "/cli-json/set_port", debug_=self.debug)
        req_json = LFUtils.portUpRequest(resource, None, debug_on=self.debug)
        req_json["port"] = self.vap_name
        set_port_r.addPostData(req_json)
        json_response = set_port_r.jsonPost(self.debug)
        time.sleep(0.03)

    def admin_down(self, resource):
        set_port_r = LFRequest.LFRequest(self.lfclient_url, "/cli-json/set_port", debug_=self.debug)
        req_json = LFUtils.port_down_request(resource, None, debug_on=self.debug)
        req_json["port"] = self.vap_name
        set_port_r.addPostData(req_json)
        json_response = set_port_r.jsonPost(self.debug)
        time.sleep(0.03)

    def use_security(self, security_type, ssid=None, passwd=None):
        types = {"wep": "wep_enable", "wpa": "wpa_enable", "wpa2": "wpa2_enable", "wpa3": "use-wpa3", "open": "[BLANK]"}
        self.add_vap_data["ssid"] = ssid
        if security_type in types.keys():
            if (ssid is None) or (ssid == ""):
                raise ValueError("use_security: %s requires ssid" % security_type)
            if (passwd is None) or (passwd == ""):
                raise ValueError("use_security: %s requires passphrase or [BLANK]" % security_type)
            for name in types.values():
                if name in self.desired_add_vap_flags and name in self.desired_add_vap_flags_mask:
                    self.desired_add_vap_flags.remove(name)
                    self.desired_add_vap_flags_mask.remove(name)
            if security_type != "open":
                self.desired_add_vap_flags.append(types[security_type])
                self.desired_add_vap_flags_mask.append(types[security_type])
            else:
                passwd = "[BLANK]"
            self.set_command_param("add_vap", "ssid", ssid)
            self.set_command_param("add_vap", "key", passwd)
            # unset any other security flag before setting our present flags
            if security_type == "wpa3":
                self.set_command_param("add_vap", "ieee80211w", 2)

    def set_command_flag(self, command_name, param_name, value):
        # we have to check what the param name is
        if (command_name is None) or (command_name == ""):
            return
        if (param_name is None) or (param_name == ""):
            return
        if command_name not in self.COMMANDS:
            print("Command name name [%s] not defined in %s" % (command_name, self.COMMANDS))
            return
        if command_name == "add_vap":
            if (param_name not in add_vap.add_vap_flags):
                print("Parameter name [%s] not defined in add_vap.py" % param_name)
                if self.debug:
                    pprint(add_vap.add_vap_flags)
                return
            if (value == 1) and (param_name not in self.desired_add_vap_flags):
                self.desired_add_vap_flags.append(param_name)
                self.desired_add_vap_flags_mask.append(param_name)
            elif value == 0:
                self.desired_add_vap_flags.remove(param_name)
                self.desired_add_vap_flags_mask.append(param_name)

        elif command_name == "set_port":
            if (param_name not in set_port.set_port_current_flags) and (
                    param_name not in set_port.set_port_cmd_flags) and (
                    param_name not in set_port.set_port_interest_flags):
                print("Parameter name [%s] not defined in set_port.py" % param_name)
                if self.debug:
                    pprint(set_port.set_port_cmd_flags)
                    pprint(set_port.set_port_current_flags)
                    pprint(set_port.set_port_interest_flags)
                return
            if param_name in set_port.set_port_cmd_flags:
                if (value == 1) and (param_name not in self.desired_set_port_cmd_flags):
                    self.desired_set_port_cmd_flags.append(param_name)
                elif value == 0:
                    self.desired_set_port_cmd_flags.remove(param_name)
            elif param_name in set_port.set_port_current_flags:
                if (value == 1) and (param_name not in self.desired_set_port_current_flags):
                    self.desired_set_port_current_flags.append(param_name)
                elif value == 0:
                    self.desired_set_port_current_flags.remove(param_name)
            elif param_name in set_port.set_port_interest_flags:
                if (value == 1) and (param_name not in self.desired_set_port_interest_flags):
                    self.desired_set_port_interest_flags.append(param_name)
                elif value == 0:
                    self.desired_set_port_interest_flags.remove(param_name)
            else:
                raise ValueError("Unknown param name: " + param_name)

    def set_command_param(self, command_name, param_name, param_value):
        # we have to check what the param name is
        if (command_name is None) or (command_name == ""):
            return
        if (param_name is None) or (param_name == ""):
            return
        if command_name not in self.COMMANDS:
            self.error("Command name name [%s] not defined in %s" % (command_name, self.COMMANDS))
            return
        if command_name == "add_vap":
            self.add_vap_data[param_name] = param_value
        elif command_name == "set_port":
            self.set_port_data[param_name] = param_value

    def add_named_flags(self, desired_list, command_ref):
        if desired_list is None:
            raise ValueError("addNamedFlags wants a list of desired flag names")
        if len(desired_list) < 1:
            print("addNamedFlags: empty desired list")
            return 0
        if (command_ref is None) or (len(command_ref) < 1):
            raise ValueError("addNamedFlags wants a maps of flag values")

        result = 0
        for name in desired_list:
            if (name is None) or (name == ""):
                continue
            if name not in command_ref:
                if self.debug:
                    pprint(command_ref)
                raise ValueError("flag %s not in map" % name)
            # print("add-named-flags: %s  %i"%(name, command_ref[name]))
            result |= command_ref[name]

        return result

    def create(self, resource, radio, channel=None, up_=None, debug=False, use_ht40=True, use_ht80=True,
               use_ht160=False,
               suppress_related_commands_=True, use_radius=False, hs20_enable=False, bridge=True):
        port_list = self.local_realm.json_get("port/1/1/list")
        if port_list is not None:
            port_list = port_list['interfaces']
            for port in port_list:
                for k, v in port.items():
                    if v['alias'] == self.vap_name:
                        self.local_realm.rm_port(v['port'], check_exists=True)
        if use_ht160:
            self.desired_add_vap_flags.append("enable_80211d")
            self.desired_add_vap_flags_mask.append("enable_80211d")
            self.desired_add_vap_flags.append("80211h_enable")
            self.desired_add_vap_flags_mask.append("80211h_enable")
            self.desired_add_vap_flags.append("ht160_enable")
            self.desired_add_vap_flags_mask.append("ht160_enable")
        if not use_ht40:
            self.desired_add_vap_flags.append("disable_ht40")
            self.desired_add_vap_flags_mask.append("disable_ht40")
        if not use_ht80:
            self.desired_add_vap_flags.append("disable_ht80")
            self.desired_add_vap_flags_mask.append("disable_ht80")
        if use_radius:
            self.desired_add_vap_flags.append("8021x_radius")
            self.desired_add_vap_flags_mask.append("8021x_radius")
        if hs20_enable:
            self.desired_add_vap_flags.append("hs20_enable")
            self.desired_add_vap_flags_mask.append("hs20_enable")

        # print("MODE ========= ", self.mode)

        jr = self.local_realm.json_get("/radiostatus/1/%s/%s?fields=channel,frequency,country" % (resource, radio),
                                       debug_=self.debug)
        if jr is None:
            raise ValueError("No radio %s.%s found" % (resource, radio))

        eid = "1.%s.%s" % (resource, radio)
        frequency = 0
        country = 0
        if eid in jr:
            country = jr[eid]["country"]

        data = {
            "shelf": 1,
            "resource": resource,
            "radio": radio,
            "mode": self.mode,  # "NA", #0 for AUTO or "NA"
            "channel": channel,
            "country": country,
            "frequency": self.local_realm.channel_freq(channel_=channel)
        }
        self.local_realm.json_post("/cli-json/set_wifi_radio", _data=data)
        if up_ is not None:
            self.up = up_
        if self.up:
            if "create_admin_down" in self.desired_add_vap_flags:
                del self.desired_add_vap_flags[self.desired_add_vap_flags.index("create_admin_down")]
        elif "create_admin_down" not in self.desired_add_vap_flags:
            self.desired_add_vap_flags.append("create_admin_down")

        # create vaps down, do set_port on them, then set vaps up
        self.add_vap_data["mode"] = self.mode
        self.add_vap_data["flags"] = self.add_named_flags(self.desired_add_vap_flags, add_vap.add_vap_flags)
        self.add_vap_data["flags_mask"] = self.add_named_flags(self.desired_add_vap_flags_mask, add_vap.add_vap_flags)
        self.add_vap_data["radio"] = radio

        self.add_vap_data["resource"] = resource
        self.set_port_data["current_flags"] = self.add_named_flags(self.desired_set_port_current_flags,
                                                                   set_port.set_port_current_flags)
        self.set_port_data["interest"] = self.add_named_flags(self.desired_set_port_interest_flags,
                                                              set_port.set_port_interest_flags)
        # these are unactivated LFRequest objects that we can modify and
        # re-use inside a loop, reducing the number of object creations
        add_vap_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/add_vap")
        set_port_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/set_port")
        wifi_extra_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/set_wifi_extra")
        if suppress_related_commands_:
            self.add_vap_data["suppress_preexec_cli"] = "yes"
            self.add_vap_data["suppress_preexec_method"] = 1
            self.set_port_data["suppress_preexec_cli"] = "yes"
            self.set_port_data["suppress_preexec_method"] = 1

        # pprint(self.station_names)
        # exit(1)
        self.set_port_data["port"] = self.vap_name
        self.add_vap_data["ap_name"] = self.vap_name
        add_vap_r.addPostData(self.add_vap_data)
        if debug:
            print("- 1502 - %s- - - - - - - - - - - - - - - - - - " % self.vap_name)
            pprint(self.add_vap_data)
            pprint(self.set_port_data)
            pprint(add_vap_r)
            print("- ~1502 - - - - - - - - - - - - - - - - - - - ")

        json_response = add_vap_r.jsonPost(debug)
        # time.sleep(0.03)
        time.sleep(2)
        set_port_r.addPostData(self.set_port_data)
        json_response = set_port_r.jsonPost(debug)
        time.sleep(0.03)

        self.wifi_extra_data["resource"] = resource
        self.wifi_extra_data["port"] = self.vap_name
        if self.wifi_extra_data_modified:
            wifi_extra_r.addPostData(self.wifi_extra_data)
            json_response = wifi_extra_r.jsonPost(debug)

        port_list = self.local_realm.json_get("port/1/1/list")
        if port_list is not None:
            port_list = port_list['interfaces']
            for port in port_list:
                for k, v in port.items():
                    if v['alias'] == 'br0':
                        self.local_realm.rm_port(k, check_exists=True)
                        time.sleep(5)

        # create bridge
        if bridge :
            print("creating bridge")
            data = {
                "shelf": 1,
                "resource": resource,
                "port": "br0",
                "network_devs": "eth1,%s" % self.vap_name
            }
            self.local_realm.json_post("cli-json/add_br", data)

            bridge_set_port = {
                "shelf": 1,
                "resource": resource,
                "port": "br0",
                "current_flags": 0x80000000,
                "interest": 0x4000  # (0x2 + 0x4000 + 0x800000)  # current, dhcp, down
            }
            self.local_realm.json_post("cli-json/set_port", bridge_set_port)

        if (self.up):
            self.admin_up(resource)

    def modify(self, radio):
        self.add_vap_data["flags"] = self.add_named_flags(self.desired_add_vap_flags, add_vap.add_vap_flags)
        self.add_vap_data["flags_mask"] = self.add_named_flags(self.desired_add_vap_flags_mask, add_vap.add_vap_flags)
        self.add_vap_data["radio"] = radio
        self.add_vap_data["ap_name"] = self.vap_name
        self.add_vap_data["ssid"] = 'NA'
        self.add_vap_data["key"] = 'NA'
        self.add_vap_data['mac'] = 'NA'

        add_vap_r = LFRequest.LFRequest(self.lfclient_url + "/cli-json/add_vap")
        if self.debug:
            print(self.add_vap_data)
        add_vap_r.addPostData(self.add_vap_data)
        json_response = add_vap_r.jsonPost(self.debug)


    def cleanup(self, resource, delay=0.03):
        print("Cleaning up VAPs")
        desired_ports = ["1.%s.%s" % (resource, self.vap_name), "1.%s.br0" % resource]

        del_count = len(desired_ports)

        # First, request remove on the list.
        for port_eid in desired_ports:
            self.local_realm.rm_port(port_eid, check_exists=True)

        # And now see if they are gone
        LFUtils.wait_until_ports_disappear(base_url=self.lfclient_url, port_list=desired_ports)

