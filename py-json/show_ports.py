# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# example of how to check a LANforge json url                                       -
#                                                                                   -
# the syntax of the request is /port/<shelf=1>/<resource=1>/<list|all|portid>       -
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import sys
import os
import importlib
import json
import pprint

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()

if 'lanforge-scripts' not in sys.path:
    sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../../")))

LFRequest = importlib.import_module("lanforge-scripts.py-json.LANforge.LFRequest")


def main():
   url = "http://localhost:8080/port/1/1/list"
   timeout = 5 # seconds

   lf_r = LFRequest.LFRequest(url)
   json_response = lf_r.getAsJson(True)
   j_printer = pprint.PrettyPrinter(indent=2)
   j_printer.pprint(json_response)
   
   #for record in json_response['interfaces']:
        #j_printer.pprint(record)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == "__main__":
   main()
#
