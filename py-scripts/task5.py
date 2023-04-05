import sys
import os
import importlib
import argparse
import pprint
import requests
import time



from create_station import CreateStation
from create_l3 import CreateL3
from gp_genric import PingTest


sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))
LFUtils = importlib.import_module("py-json.LANforge.LFUtils")
realm = importlib.import_module("py-json.realm")
Realm = realm.Realm
lf_clean = importlib.import_module("py-scripts.lf_cleanup")
gentest = importlib.import_module("py-json.gen_cxprofile")


parser = argparse.ArgumentParser(description="create station and run layer 3 traffic between them")
parser.add_argument('--sta', type=int, help= 'type no of stations to create', default=2)
parser.add_argument('--ssid', type=str, help= 'ssid name', default="Netgear_5g")
parser.add_argument('--psswd', type=str, help= 'password', default="lanforge")
parser.add_argument('--sec', type=str, help= 'security', default="wpa2")
parser.add_argument('--mode', type=int, help= 'channel mode, 0 is auto', default=0)
parser.add_argument('--mgr', type=str, help= 'Lanforge ip', default="192.168.200.37")
parser.add_argument('--radio', type=str, help= 'radio',default="wiphy1")
parser.add_argument('--endp_a', type=str, help= 'endpoint a in l3', default= "sta0001")
parser.add_argument('--endp_b', type=str, help= 'endpoint b in l3',default="eth1")
parser.add_argument('--minr_a', type=int, help= 'minimum data rate for endpoint a',default=20000)
parser.add_argument('--minr_b', type=int, help= 'minimum data rate for endpoint a',default=30000)
parser.add_argument('--upstream', type=str, help= 'upstream port',default="eth1")
parser.add_argument('--dest', type=str, help= 'generic tab destination port',default="192.168.1.1")
parser.add_argument('--ping', type=int, help= 'number of pings',default=10)
parser.add_argument('--port', type=int, help= 'port number',default=8080)

'''example
python task_2.py --mgr "192.168.200.81" --ssid "ASUS_5G" --psswd "Password@123" --sec "wpa2" --mode 0 --sta 2 --radio "wiphy1" --endp_a "sta0001" --endp_b "eth1" --minr_a 1000 --minr_b 30000'''
args = parser.parse_args()
start_id = 0
station_list = LFUtils.port_name_series(prefix="sta",
                                            start_id=start_id,
                                            end_id=start_id + args.sta - 1,
                                            padding_number=10000)

#create stations
create_station = CreateStation(_host=args.mgr,
                                   _port=8080,
                                   _ssid=args.ssid,
                                   _password=args.psswd,
                                   _security= args.sec,
                                   _mode=args.mode,
                                   _sta_list= station_list,
                                   _radio=args.radio,
                                   _set_txo_data=None)
#Pre-cleanup for stations
obj = lf_clean.lf_clean(host=args.mgr,
                            port=8080,
                            clean_cxs=True,
                            clean_sta=True)
obj.resource = "all"
obj.cxs_clean()
obj.sta_clean()
create_station.build()
print("sleepig for 5 sec")
time.sleep(5)


#create layer3 cross-connections
ip_var_test = CreateL3(host=args.mgr,
                           port=8080,
                           name_prefix="VT",
                           endp_a=station_list,
                           endp_b=args.endp_b,
                           min_rate_a=args.minr_a,
                           min_rate_b=args.minr_b,
                           mode=args.mode)
ip_var_test.pre_cleanup()
ip_var_test.build()

#find the ip of the stations
class ipfinder:
    def get_ips(self, keys):
        x = requests.get("http://" + args.mgr + ":" + str(args.port) + "/ports/all").json()
        ips_list = []
        for interface in x["interfaces"]:
            for key in keys:
                if key in interface.keys():
                    ips_list.append(interface[key]["ip"])
        return ips_list

ip = ipfinder()
keys = ["1.1." + item for item in station_list]
print ("keys after prefix :" , keys)
ips = ip.get_ips(keys)
print(ips)


'''#create cross connections for ping
generic_test = PingTest(host=args.mgr, 
                       port=8080,
                           #number_template="00",
                           radio=args.radio,
                           sta_list=station_list,
                           name_prefix="GT",
                           test_type="lfping",
                           interval=1,
                           ssid=args.ssid,
                           passwd=args.psswd,
                           security=args.sec,
                           upstream=args.upstream,                           
                           dest=ips[0],
                           speedtest_min_up=args.minr_a,
                           speedtest_min_dl=args.minr_b,
                           speedtest_max_ping=25,
                           client=None)
generic_test.cleanup(station_list)
generic_test.build()
generic_test.start()
'''
'''gentest.create_gen(sta_port=keys,dest=ips[0], sleep_time=.5)
gentest.create()
'''
# Get LANforge client URL
lfclient_url = "http://%s:%d" % (args.mgr, args.port)

# Create generator
gen = gentest.create_gen(lfclient_url=lfclient_url, resource=keys[0], dest=ips[0], sleep_time=.5)

# Start generator
gen.start()