#!/usr/bin/env python3
# Create Layer-3 Cross Connection Using LANforge JSON AP : https://www.candelatech.com/cookbook.php?vol=fire&book=scripted+layer-3+test
# Written by Candela Technologies Inc.
# Updated by: Erin Grimes

"""
Example Command:
./create_l3.py --endp_a 'eth1' --endp_b 'eth2' --min_rate_a '56000' --min_rate_b '40000'
"""

import sys
import importlib
import os
if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)
# if 'py-json' not in sys.path:
#     sys.path.append(os.path.join(os.path.abspath('..'), 'py-json'))
if 'lanforge-scripts' not in sys.path:
    sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../../")))
LANforge = importlib.import_module("lanforge-scripts.py-json.LANforge")
import argparse
# from LANforge.lfcli_base import LFCliBase
# from lfcli_base import *
lfcli_base = importlib.import_module("lanforge-scripts.py-json.LANforge.lfcli_base")
LFCliBase = lfcli_base.LFCliBase
# from LANforge import LFUtils
LFUtils = importlib.import_module("lanforge-scripts.py-json.LANforge.LFUtils")
# from realm import Realm
realm = importlib.import_module("lanforge-scripts.py-json.realm")
Realm = realm.Realm
# from realm import TestGroupProfile
TestGroupProfile = realm.TestGroupProfile
import time
import datetime


class CreateL3(Realm):
    def __init__(self,
                 # ssid, security, password, radio,
                 # sta_list,
                 name_prefix,
                 # upstream,
                 endp_b,
                 endp_a,
                 host="localhost", port=8080, mode=0,
                 # ap=None,
                 min_rate_a=56, max_rate_a=0,
                 min_rate_b=56, max_rate_b=0,
                 # number_template="00000", use_ht160=False,
                 _debug_on=False,
                 _exit_on_error=False,
                 _exit_on_fail=False):
        super().__init__(host, port)
        # self.upstream = upstream
        self.host = host
        self.port = port
        self.endp_b = endp_b
        self.endp_a = endp_a
        # self.ssid = ssid
        # self.sta_list = sta_list
        # self.security = security
        # self.password = password
        # self.radio = radio
        self.mode = mode
        # self.ap = ap
        # self.number_template = number_template
        # self.debug = _debug_on
        self.name_prefix = name_prefix
        self.station_profile = self.new_station_profile()
        self.cx_profile = self.new_l3_cx_profile()
        self.station_profile.lfclient_url = self.lfclient_url
        # self.station_profile.ssid = self.ssid
        # self.station_profile.ssid_pass = self.password
        # self.station_profile.security = self.security
        # self.station_profile.number_template_ = self.number_template
        # self.station_profile.debug = self.debug
        # self.station_profile.use_ht160 = use_ht160
        # if self.station_profile.use_ht160:
        #     self.station_profile.mode = 9
        # self.station_profile.mode = mode
        # if self.ap is not None:
        #     self.station_profile.set_command_param("add_sta", "ap", self.ap)
        self.station_list= LFUtils.portNameSeries(prefix_="sta", start_id_=0, end_id_=2, padding_number_=10000, radio='wiphy0') #Make radio a user defined variable from terminal.

        self.cx_profile.host = self.host
        self.cx_profile.port = self.port
        self.cx_profile.name_prefix = self.name_prefix
        self.cx_profile.side_a_min_bps = min_rate_a
        self.cx_profile.side_a_max_bps = max_rate_a
        self.cx_profile.side_b_min_bps = min_rate_b
        self.cx_profile.side_b_max_bps = max_rate_b

    def pre_cleanup(self):
        self.cx_profile.cleanup_prefix()
        # for sta in self.sta_list:
        #     self.rm_port(sta, check_exists=True)

    def build(self):

        # self.station_profile.use_security(self.security,
        #                                   self.ssid,
        #                                   self.password)
        # self.station_profile.set_number_template(self.number_template)
        # print("Creating stations")
        # self.station_profile.set_command_flag("add_sta", "create_admin_down", 1)
        # self.station_profile.set_command_param("set_port", "report_timer", 1500)
        # self.station_profile.set_command_flag("set_port", "rpt_timer", 1)
        # self.station_profile.create(radio=self.radio,
        #                             sta_names_=self.sta_list,
        #                             debug=self.debug)
        self.cx_profile.create(endp_type="lf_udp",
                               side_a=self.endp_a,
                               side_b=self.endp_b,
                               sleep_time=0)
        self._pass("PASS: Cross-connect build finished")


def main():
    parser = LFCliBase.create_basic_argparse(
        prog='create_l3.py',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''\
            Generate traffic between ports
            ''',

        description='''\
        ''')

    required_args = None
    for group in parser._action_groups:
        if group.title == "required arguments":
            required_args = group
            break;
    if required_args is not None:
        required_args.add_argument('--min_rate_a', help='--min_rate_a bps rate minimum for side_a', default=56000)
        required_args.add_argument('--min_rate_b', help='--min_rate_b bps rate minimum for side_b', default=56000)
        required_args.add_argument('--endp_a', help='--endp_a station list', default=["eth1"], action="append")
        required_args.add_argument('--endp_b', help='--upstream port', default="eth2")

    optional_args = None
    for group in parser._action_groups:
        if group.title == "optional arguments":
            optional_args = group
            break;
    if optional_args is not None:
        optional_args.add_argument('--mode', help='Used to force mode of stations')
        # optional_args.add_argument('--ap', help='Used to force a connection to a particular AP')
        # optional_args.add_argument('--number_template', help='Start the station numbering with a particular number. Default is 0000', default=0000)
    args = parser.parse_args()

    num_sta = 2
    if (args.num_stations is not None) and (int(args.num_stations) > 0):
        num_sta = int(args.num_stations)

    # station_list = LFUtils.portNameSeries(prefix_="sta", start_id_=int(args.number_template), end_id_=num_sta+int(args.number_template) - 1, padding_number_=10000,
    #                                       radio=args.radio)
    ip_var_test = CreateL3(host=args.mgr,
                           port=args.mgr_port,
                           # number_template=str(args.number_template),
                           name_prefix="VT",
                           endp_a=args.endp_a,
                           endp_b=args.endp_b,
                           # ssid=args.ssid,
                           # password=args.passwd,
                           # radio=args.radio,
                           # security=args.security,
                           # use_ht160=False,
                           min_rate_a=args.min_rate_a,
                           min_rate_b=args.min_rate_b,
                           mode=args.mode,
                           # ap=args.ap,
                           _debug_on=args.debug)

    ip_var_test.pre_cleanup()
    ip_var_test.build()
    if not ip_var_test.passes():
        print(ip_var_test.get_fail_message())
        ip_var_test.exit_fail()
    print('Creates %s stations and connections' % num_sta)


if __name__ == "__main__":
    main()
