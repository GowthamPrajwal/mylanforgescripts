#!/usr/bin/env python3
'''
File: read kpi.csv place in sql database, create png of historical kpi and present graph on dashboard
Usage: kpi_csv_sq.py --store --png --show --path <path to directories to traverse> --database <name of database> 
Example: kpi_csv_sq.py --show  (show dashboard generated from database)
Example: kpi_csv_sq.py --store --png --show --path <path to read kpi.csv> (read kpi.csv store to database, write png, show dashboard )

'''
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import sqlite3
import argparse
from  pathlib import Path
import time

# lf_report is from the parent of the current file
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from lf_report import lf_report

sys.path.append('/')


# Any style components can be used
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

class csv_sqlite_dash():
    def __init__(self,
                _path = '.',
                _file = 'kpi.csv',
                _database = 'qa_db',
                _table = 'qa_table',
                _server = 'http://192.168.95.6/',
                _png = False):
        self.path = _path
        self.file = _file
        self.database = _database
        self.table = _table
        self.server = _server
        self.png = _png
        self.png_generated = False
        self.kpi_list = []
        self.html_list = []
        self.conn = None
        self.df = pd.DataFrame()
        self.plot_figure = []
        self.children_div = []
        self.html_results =""
        self.server_html_reports = self.server + 'html-reports/' 
        self.server_started = False
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
        # https://community.plotly.com/t/putting-a-dash-instance-inside-a-class/6097/3
        #https://dash.plotly.com/dash-html-components/button
        #self.app.callback(dash.dependencies.Output('container-button-basic', 'children'),
        #                [dash.dependencies.Input(component_id ='submit-val', component_property ='n_clicks')])(self.show)

    # information on sqlite database
    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
    def store(self):
        print("reading kpi and storing in db {}".format(self.database))
        path = Path(self.path)
        self.kpi_list = list(path.glob('**/kpi.csv'))  # Hard code for now 

        if not self.kpi_list:
            print("WARNING: used --store , no new kpi.csv found, check input path or remove --store from command line")

        for kpi in self.kpi_list: #TODO note empty kpi.csv failed test 
            df_kpi_tmp = pd.read_csv(kpi, sep='\t')  
            df_kpi_tmp['kpi_path'] = str(kpi).replace('kpi.csv','')  # only store the path to the kpi.csv file
            df_kpi_tmp = df_kpi_tmp.append(df_kpi_tmp, ignore_index=True)
            self.df = self.df.append(df_kpi_tmp, ignore_index=True)

        self.conn = sqlite3.connect(self.database) 
        try:
            self.df.to_sql(self.table,self.conn,if_exists='append')
        except:
            print("attempt to append to database with different column layout, casused exception, input new name --database <new name>")            
            exit(1)
        self.conn.close()

    def generate_graph_png(self):
        print("generating graphs to display")
        print("generate_graph_png: {}".format(time.time()))

        #https://datacarpentry.org/python-ecology-lesson/09-working-with-sql/index.html-
        self.conn = sqlite3.connect(self.database)
        df3 = pd.read_sql_query("SELECT * from {}".format(self.table) ,self.conn) #current connection is sqlite3 /TODO move to SQLAlchemy
        # sort by date column
        try:
            df3 = df3.sort_values(by='Date')
        except:
            print("Database empty: KeyError(key) when sorting by Date, check Database name, path to kpi, typo in path, exiting")
            exit(1)
        self.conn.close()

        # graph group and test-tag are used for detemining the graphs, can use any columns
        # the following list manipulation removes the duplicates
        graph_group_list = list(df3['Graph-Group'])
        graph_group_list = list(set(graph_group_list)) 

        test_tag_list = list(df3['test-tag'])
        test_tag_list = list(set(test_tag_list))
        
        test_rig_list = list(df3['test-rig'])
        test_rig_list = list(set(test_rig_list))

        self.children_div.append(html.A('html_reports', href=self.server_html_reports, target='_blank'))
        for test_rig in test_rig_list:
            for test_tag in test_tag_list:
                for group in graph_group_list:
                    df_tmp = df3.loc[(df3['test-rig'] == test_rig) & (df3['Graph-Group'] == str(group)) & (df3['test-tag'] == str(test_tag))]
                    if df_tmp.empty == False:
                        kpi_fig = (px.scatter(df_tmp, x="Date", y="numeric-score",
                             color="short-description", hover_name="short-description",
                             size_max=60)).update_traces(mode='lines+markers')

                        df_tmp = df_tmp.sort_values(by='Date')
                        test_id_list = list(df_tmp['test-id'])
                        kpi_path_list = list(df_tmp['kpi_path'])
                        # get Device Under Test Information
                        dut_model_num_list = list(df_tmp['dut-model-num'])
                        dut_sw_version_list = list(df_tmp['dut-sw-version'])
                        dut_hw_version_list = list(df_tmp['dut-hw-version'])
                        dut_serial_num_list = list(df_tmp['dut-serial-num'])

                        units_list = list(df_tmp['Units'])

                        kpi_fig.update_layout(
                            title="{} : {} : {} : {} : {} : {} : {} : {}".format(test_id_list[-1], group, test_tag, test_rig, 
                                dut_model_num_list[-1], dut_sw_version_list[-1],dut_hw_version_list[-1],dut_serial_num_list[-1]),
                            xaxis_title="Time",
                            yaxis_title="{}".format(units_list[-1]),
                            xaxis = {'type' : 'date'}
                        )
                        # save the figure - figures will be over written png 
                        # for testing 
                        png_server_img = ''
                        if self.png:
                            if self.png_generated:
                                pass
                            else:
                                print("generating png files")
                                print("kpi_path:{}".format(df_tmp['kpi_path']))
                                png_path = os.path.join(kpi_path_list[-1],"kpi.png") # use simple names {}_{}_{}_{}_kpi.png".format(test_id_list[-1], group, test_tag, test_rig))
                                html_path = os.path.join(kpi_path_list[-1],"kpi.html") # use simple names {}_{}_{}_{}_kpi.html".format(test_id_list[-1], group, test_tag, test_rig))
                                print("png_path {}".format(png_path))
                                png_server_img = self.server + png_path.replace('/home/lanforge','')
                                print("png_server_img {}".format(png_server_img))
                                kpi_fig.write_image(png_path,scale=1,width=1200,height=350)
                                #https://plotly.com/python/interactive-html-export/
                                kpi_fig.write_html(html_path)
                                # png of graph data to display
                                self.children_div.append(html.Img(src=png_server_img))
                                # may need .css class for formatting the images
                                self.html_results += """
                                <img src={png_server_img}>
                                """.format(png_server_img=png_server_img)

                        # use image from above to creat html display - this uses dynamic graphing
                        #self.children_div.append(dcc.Graph(figure=kpi_fig))

                        #TODO the link must be to a server to display html
                        # WARNING: DO NOT USE os.path.join will use the path for where the script is RUN which can be container.
                        # need to construct path to server manually. 
                        #TODO need to work out the reporting paths - pass in path adjust
                        self.children_div.append(html.Br())
                        self.html_results +="""<br>"""

                        # link to interactive results
                        kpi_html_path = self.server + kpi_path_list[-1] + "kpi.html"
                        kpi_html_path = kpi_html_path.replace('/home/lanforge/','')
                        self.children_div.append(html.Br())
                        self.html_results +="""<br>"""
                        self.children_div.append(html.A('{}_{}_{}_{}_kpi.html'.format(test_id_list[-1], group, test_tag, test_rig),
                            href=kpi_html_path, target='_blank'))
                        self.html_results +="""<a href={kpi_html_path}>{test_id}_{group}_{test_tag}_{test_rig}_kpi.html<a>
                        """.format(kpi_html_path=kpi_html_path,test_id=test_id_list[-1], group=group, test_tag=test_tag, test_rig=test_rig)

                        # link to full test results
                        report_index_html_path = self.server + kpi_path_list[-1] + "index.html"
                        report_index_html_path = report_index_html_path.replace('/home/lanforge/','')
                        self.children_div.append(html.Br())
                        self.html_results +="""<br>"""
                        self.children_div.append(html.A('{}_{}_{}_{}_report.html'.format(test_id_list[-1], group, test_tag, test_rig),
                            href=report_index_html_path, target='_blank'))
                        self.html_results +="""<a href={report_index_html_path}>{test_id}_{group}_{test_tag}_{test_rig}_report.html<a>
                        """.format(report_index_html_path=report_index_html_path,test_id=test_id_list[-1], group=group, test_tag=test_tag, test_rig=test_rig)
                        self.children_div.append(html.Br())
                        self.children_div.append(html.Br())
                        self.children_div.append(html.Br())
                        self.html_results +="""<br>"""
                        self.html_results +="""<br>"""
                        self.html_results +="""<br>"""

        
        # TODO see if this stops the regenration of the graphs each time
        self.png_generated = True


    # access from server
    # https://stackoverflow.com/questions/61678129/how-to-access-a-plotly-dash-app-server-via-lan
    #def show(self,n_clicks):
    def show(self):
        #print("refreshes: {}".format(n_clicks))
        self.generate_graph_png()
        if not self.children_div:
            print("NOTE: test-tag may not be present in the kpi thus no results generated")
        print("show: {}".format(time.time()))
        self.app.layout = html.Div([
            html.Div(id='my-output'),
            html.H1(children= "LANforge Testing",className="lanforge",
            style={'color':'green','text-align':'center'}),
            #html.Button('Submit Recalculate',id='submit-val', n_clicks=0),
            #html.Div(id='container-button-basic', children='to recalculate hit submit'),
            html.H2(children= "Results",className="ts1",
            style={'color':'#00361c','text-align':'left'}),
            # images_div is already a list, children = a list of html components
            # remove scrolling : html.Div(children= self.children_div, style={"maxHeight": "600px", "overflow": "scroll"} ), 
            html.Div(children= self.children_div ), 
            html.A('www.candelatech.com',href='http://www.candelatech.com', target='_blank',
            style={'color':'#00361c','text-align':'left'}),
        ])

        # save as standalone files
        #https://plotly.com/python/static-image-export/
        
        if self.server_started:
            print("refresh complete")
            pass
        else:
            self.server_started = True
            print("self.server_started {}".format(self.server_started))
            #NOTE: the server_started flag needs to be set prior to run_server (or you get to debug an infinite loop)
            self.app.run_server(host= '0.0.0.0', debug=True)
            # host = '0.0.0.0'  allows for remote access,  local debug host = '127.0.0.1'
            # app.run_server(host= '0.0.0.0', debug=True) 

    def get_html_results(self):
        return self.html_results

def main():

    parser = argparse.ArgumentParser(
        prog='kpi_csv_sq.py',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''\
        read kpi.csv into sqlite database , save png of history and preset on dashboard

            ''',
        description='''\
File: read kpi.csv place in sql database, create png of historical kpi and present graph on dashboard
Usage: kpi_csv_sq.py --store --png --show --path <path to directories to traverse> --database <name of database> 
Example: kpi_csv_sq.py --show  (show dashboard generated from database)
Example: kpi_csv_sq.py --store --png --show --path <path to read kpi.csv> (read kpi.csv store to database, write png, show dashboard )

        ''')
    parser.add_argument('--path', help='--path top directory path to kpi if regererating database or png files',default='')
    parser.add_argument('--file', help='--file kpi.csv  default: kpi.csv',default='kpi.csv') #TODO is this needed
    parser.add_argument('--database', help='--database qa_test_db  default: qa_test_db',default='qa_test_db')
    parser.add_argument('--table', help='--table qa_table  default: qa_table',default='qa_table')
    parser.add_argument('--server', help='--server http://<server ip>/   default: http://192.168.95.6/',default='http://192.168.95.6/')
    parser.add_argument('--store', help='--store , store kpi to db, action store_true',action='store_true')
    parser.add_argument('--png', help='--png,  generate png for kpi in path, generate display, action store_true',action='store_true')
    parser.add_argument('--show', help='--show generate display and show dashboard, action store_true',action='store_true')
    parser.add_argument('--dir', help="--dir <results directory> default lf_qa", default="lf_qa")

    
    args = parser.parse_args()

    __path = args.path
    __file = args.file
    __database = args.database
    __table = args.table
    __server = args.server
    __png = args.png
    __dir = args.dir

    # needed for refresh button 
    # n_clicks = 0

    print("config: path:{} file:{} database:{} table:{} server:{} store:{} png:{} show:{} "
        .format(__path,__file,__database,__table,__server,args.store, args.png,args.show))

    if(__path == '' and args.store == True):
        print("--path <path of kpi.csv> must be entered if --store ,  exiting")
        exit(1)

    if(args.png == True and args.store == False):
        print("if --png set to create png files then --store must also be set, exiting")
        exit(1)

    if(args.png == True and args.show == True):
        print("WARNING: generating png files will effect initial display performance")


    # create report class for reporting
    report = lf_report(_path = __path,
                       _results_dir_name =__dir,
                       _output_html="lf_qa.html",
                       _output_pdf="lf_qa.pdf" )        

    #current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    #csv_results = "lf_qa-{}.csv".format(current_time)
    #csv_results = report.file_add_path(csv_results)


    csv_dash = csv_sqlite_dash(
                _path = __path,
                _file = __file,
                _database = __database,
                _table = __table,
                _server = __server,
                _png = __png)
    if args.store:
        csv_dash.store()
    if args.png:
        csv_dash.generate_graph_png()
    if args.show:        
        #csv_dash.show(n_clicks)
        csv_dash.show()
        
    # generate output reports
    report.set_title("LF QA: Verification Test Run")
    report.build_banner_left()
    report.start_content_div2()
    report.set_obj_html("Objective", "QA Verification")
    report.build_objective()
    pdf_link_path = report.get_pdf_path()
    pdf_link_path = __server + pdf_link_path.replace('/home/lanforge/','')
    report.build_pdf_link(pdf_link_path)

    report_path = report.get_path()
    report_path = __server + report_path.replace('/home/lanforge/','')
    report.build_link(report_path,"{}".format(report_path))

    report_parent_path = report.get_parent_path()
    report_parent_path = __server + report_parent_path.replace('/home/lanforge/','')
    report.build_link(report_parent_path,"{}".format(report_parent_path))
    report.set_table_title("QA Test Results")
    report.build_table_title()
    # report.set_text("lanforge-scripts git sha: {}".format(git_sha))
    # report.build_text()
    html_results = csv_dash.get_html_results()
    report.set_custom_html(html_results)
    report.build_custom()
    report.build_footer()
    html_report = report.write_html_with_timestamp()
    print("html report: {}".format(html_report))
    try:
        report.write_pdf_with_timestamp()
    except:
        print("exception write_pdf_with_timestamp()")



    if args.store == False and args.png == False and args.show == False:
        print("Need to enter an action of --store --png --show ")

if __name__ == '__main__':
    main()
    