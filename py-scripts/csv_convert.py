#!/usr/bin/env python3
# This program is used to read in a LANforge Dataplane CSV file and output
# a csv file that works with a customer's RvRvO visualization tool.
#
# Example use case:
#
# Read in ~/text-csv-0-candela.csv, output is stored at outfile.csv
# ./py-scripts/csv_convert.py -i ~/text-csv-0-candela.csv
#
# Output is csv file with mixxed columns, top part:
# Test Run,Position [Deg],Attenuation 1 [dB], Pal Stats Endpoint 1 Control Rssi [dBm],  Pal Stats Endpoint 1 Data Rssi [dBm]

# Second part:
# Step Index,Position [Deg],Attenuation [dB],Traffic Pair 1 Throughput [Mbps]
import sys
import os
import argparse

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)

 
sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))


class CSVParcer():
    def __init__(self,csv_infile=None,csv_outfile=None):

        idx = 0
        i_atten = -1
        i_rotation = -1
        i_rxbps = -1
        i_beacon_rssi = -1
        i_data_rssi = -1
        fpo = open(csv_outfile, "w")
        with open(csv_infile) as fp:
            line = fp.readline()
            if not line:
                exit(1)
            # Read in initial line, this is the CSV headers.  Parse it to find the column indices for
            # the columns we care about.
            x = line.split(",")
            cni = 0
            for cn in x:
                if (cn == "Attenuation [dB]"):
                    i_atten = cni
                if (cn == "Position [Deg]"):
                    i_rotation = cni
                if (cn == "Throughput [Mbps]"):
                    i_rxbps = cni
                if (cn == "Beacon RSSI [dBm]"):
                    i_beacon_rssi = cni
                if (cn == "Data RSSI [dBm]"):
                    i_data_rssi = cni
                cni += 1

            # Write out out header for the new file.
            fpo.write("Test Run,Position [Deg],Attenuation 1 [dB],Pal Stats Endpoint 1 Control Rssi [dBm],Pal Stats Endpoint 1 Data Rssi [dBm]\n")

            # Read rest of the input lines, processing one at a time.  Covert the columns as
            # needed, and write out new data to the output file.
            line = fp.readline()

            bottom_half="Step Index,Position [Deg],Attenuation [dB],Traffic Pair 1 Throughput [Mbps]\n"

            test_run="1"

            step_i = 0
            while line:
                x = line.split(",")
                #print(x)
                #print([test_run, x[i_rotation], x[i_atten], x[i_beacon_rssi], x[i_data_rssi]])
                fpo.write("%s,%s,%s,%s,%s" % (test_run, x[i_rotation], x[i_atten], x[i_beacon_rssi], x[i_data_rssi]))
                bottom_half += ("%s,%s,%s,%s\n" % (step_i, x[i_rotation], x[i_atten], x[i_rxbps]))
                line = fp.readline()
                step_i += 1

            # First half is written out now, and second half is stored...
            fpo.write("\n\n# RvRvO Data\n\n")
            fpo.write(bottom_half)

def main():

    #debug_on = False
    parser = argparse.ArgumentParser(
        prog='csv_convert.py',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''\
 Useful Information:
            ''',
        
        description='''
csv_convert.py:  
    converts the candela brief csv into the data for specific customer,
        ''')

    # for testing parser.add_argument('-i','--infile', help="input file of csv data", default='text-csv-0-candela.csv')
    parser.add_argument('-i','--infile', help="input file of csv data", required=True)
    parser.add_argument('-o','--outfile', help="output file in .csv format", default='outfile.csv')


    args = parser.parse_args()
    csv_outfile_name = None

    if args.infile:
        csv_infile_name = args.infile
    if args.outfile:
        csv_outfile_name = args.outfile

    print("infile: %s  outfile: %s"%(csv_infile_name, csv_outfile_name))

    CSVParcer(csv_infile_name, csv_outfile_name)

if __name__ == "__main__":
    main()
