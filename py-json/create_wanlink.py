#!/usr/bin/python3
# Create and modify WAN Links Using LANforge JSON AP : http://www.candelatech.com/cookbook.php?vol=cli&book=JSON:+Managing+WANlinks+using+JSON+and+Python
# Written by Candela Technologies Inc.
# Updated by: Erin Grimes
import sys
import os
import importlib
import time
from time import sleep
import urllib
from urllib import error
if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()
import pprint
if 'lanforge-scripts' not in sys.path:
    sys.path.append(os.path.join(os.path.abspath('../..'), 'lanforge-scripts'))
LANforge = importlib.import_module("lanforge-scripts.py-json.LANforge")
LFRequest = importlib.import_module("lanforge-scripts.py-json.LANforge.LFRequest")
LFUtils = importlib.import_module("lanforge-scripts.py-json.LANforge.LFUtils")
# NA=importlib.import_module("lanforge-scripts.py-json.LANforge.LFUtils.NA")

j_printer = pprint.PrettyPrinter(indent=2)
# todo: this needs to change
resource_id = 1


def main(base_url, args={}):
    print(base_url)
    json_post = ""
    json_response = ""
    num_wanlinks = -1

    # see if there are old wanlinks to remove
    lf_r = LFRequest.LFRequest(base_url+"/wl/list")
    print(lf_r.get_as_json())

    # ports to set as endpoints
    port_a = "rd0a"
    port_b = "rd1a"

    try:
        json_response = lf_r.getAsJson()
        LFUtils.debug_printer.pprint(json_response)
        for key, value in json_response.items():
            if (isinstance(value, dict) and "_links" in value):
                num_wanlinks = 1
    except urllib.error.HTTPError as error:
        print("Error code "+error.code)

    # remove old wanlinks
    if (num_wanlinks > 0):
        lf_r = LFRequest.LFRequest(base_url+"/cli-json/rm_cx")
        lf_r.addPostData({
         'test_mgr': 'all',
         'cx_name': args['name']
        })
        lf_r.jsonPost()
        sleep(0.05)

        lf_r = LFRequest.LFRequest(base_url+"/cli-json/rm_endp")
        lf_r.addPostData({
           'endp_name': args['name']+"_A"
        })
        lf_r.jsonPost()
        sleep(0.05)

        lf_r = LFRequest.LFRequest(base_url+"/cli-json/rm_endp")
        lf_r.addPostData({
           'endp_name': args['name']+"_B"
        })
        lf_r.jsonPost()
        sleep(0.05)

    # create wanlink 1a
    lf_r = LFRequest.LFRequest(base_url+"/cli-json/add_wl_endp")
    lf_r.addPostData({
        'alias': args['name']+"_A",
        'shelf': 1,
        'resource': '1',
        'port': port_a,
        'latency': args['latency_A'],
        'max_rate': args['rate_A']
    })
    lf_r.jsonPost()
    sleep(0.05)

    # create wanlink 1b
    lf_r = LFRequest.LFRequest(base_url+"/cli-json/add_wl_endp")
    lf_r.addPostData({
        'alias': args['name']+"_B",
        'shelf': 1,
        'resource': '1',
        'port': port_b,
        'latency': args['latency_B'],
        'max_rate': args['rate_B']
    })
    lf_r.jsonPost()
    sleep(0.05)

    # create cx
    lf_r = LFRequest.LFRequest(base_url+"/cli-json/add_cx")
    lf_r.addPostData({
       'alias': args['name'],
       'test_mgr': 'default_tm',
       'tx_endp': args['name']+"_A",
       'rx_endp': args['name']+"_B",
    })
    lf_r.jsonPost()
    sleep(0.05)

    # start wanlink once we see it
    seen = 0
    while (seen < 1):
        sleep(1)
        lf_r = LFRequest.LFRequest(base_url+"/wl/"+args['name']+"?fields=name,state,_links")
        try:
            json_response = lf_r.getAsJson()
            if (json_response is None):
                continue
            LFUtils.debug_printer.pprint(json_response)
            for key, value in json_response.items():
                if (isinstance(value, dict)):
                    if ("_links" in value):
                        if (value["name"] == args['name']):
                            seen = 1
                        else:
                            pass
            #         else:
            #             print(" name was not wl_eg1")
            #     else:
            #         print("value lacks _links")
            # else:
            #     print("value not a dict")

        except urllib.error.HTTPError as error:
            print("Error code "+error.code)
            continue

    print("starting wanlink:")
    # print("the latency is {laten}".format(laten=latency))
    lf_r = LFRequest.LFRequest(base_url+"/cli-json/set_cx_state")
    lf_r.addPostData({
       'test_mgr': 'all',
       'cx_name': args['name'],
       'cx_state': 'RUNNING'
    })
    lf_r.jsonPost()

    running = 0
    while (running < 1):
        sleep(1)
        lf_r = LFRequest.LFRequest(base_url+"/wl/"+args['name']+"?fields=name,state,_links")
        try:
            json_response = lf_r.getAsJson()
            if (json_response is None):
                continue
            for key, value in json_response.items():
                if (isinstance(value, dict)):
                    if ("_links" in value):
                        if (value["name"] == args['name']):
                            if (value["state"].startswith("Run")):
                                LFUtils.debug_printer.pprint(json_response)
                                running = 1

        except urllib.error.HTTPError as error:
            print("Error code "+error.code)
            continue

    print("Wanlink is running")

    # stop wanlink
    lf_r = LFRequest.LFRequest(base_url+"/cli-json/set_cx_state")
    lf_r.addPostData({
       'test_mgr': 'all',
       'cx_name': args['name'],
       'cx_state': 'STOPPED'
    })
    lf_r.jsonPost()
    running = 1
    while (running > 0):
        sleep(1)
        lf_r = LFRequest.LFRequest(base_url+"/wl/"+args['name']+"?fields=name,eid,state,_links")
        LFUtils.debug_printer.pprint(json_response)
        try:
            json_response = lf_r.getAsJson()
            if (json_response is None):
                continue
            for key, value in json_response.items():
                if (isinstance(value, dict)):
                    if ("_links" in value):
                        if (value["name"] == args['name']):
                            if (value["state"].startswith("Stop")):
                                LFUtils.debug_printer.pprint(json_response)
                                running = 0

        except urllib.error.HTTPError as error:
            print("Error code "+error.code)
            continue

    print("Wanlink is stopped.")

    # print("Wanlink info:")
    # lf_r = LFRequest.LFRequest(base_url+"/wl/wl_eg1")
    # json_response = lf_r.getAsJson()
    # LFUtils.debug_printer.pprint(json_response)

    # lf_r = LFRequest.LFRequest(base_url+"/wl_ep/wl_eg1-A")
    # json_response = lf_r.getAsJson()
    # LFUtils.debug_printer.pprint(json_response)

    # lf_r = LFRequest.LFRequest(base_url+"/wl_ep/wl_eg1-B")
    # json_response = lf_r.getAsJson()
    # LFUtils.debug_printer.pprint(json_response)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


if __name__ == '__main__':
    main()
