#!/usr/bin/env python
u"""
Known issues:
* It does not delete de temporary folder
* I/O metrics change of units when Docker thinks it's the time to do so. It won't work very well with Pandora FMS' static unit system, so a post-process should be done in this script.
"""
import subprocess, os, time

TENTACLE_CLIENT= '/usr/bin/tentacle_client' #Enter the full path to your tentacle client
SERVER_IP = 'x.x.x.x' #Enter your Pandora Server URL here

def move_file(src_path,dst_path):
        os.rename(src_path,dst_path)

def print_module(module_name,data,is_incremental=False,units=""):
        print "<module>"
        print "<name><![CDATA["+module_name+"]]></name>"
        if is_incremental:
                print "<type><![CDATA[generic_data_inc]]></type>"
        else:
                print "<type><![CDATA[generic_data]]></type>";
        print "<data><![CDATA["+data+"]]></data>"
        if units != "":
                print"<unit>"+units+"</unit>"
        print "</module>"

def print_module_to_file(module_name,data,f,is_incremental=False,units=""):
        f.write("<module>\n")
        f.write("<name><![CDATA["+module_name+"]]></name>\n")
        if is_incremental:
                f.write("<type><![CDATA[generic_data_inc]]></type>\n")
        else:
                f.write("<type><![CDATA[generic_data]]></type>\n")
        f.write("<data><![CDATA["+data+"]]></data>\n")
        if units != "":
                f.write("<unit>"+units+"</unit>\n")
        f.write("</module>\n")


def print_agent_xml(agent_name,modules,to_file=None):
        import datetime, os
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not to_file:
                print '<?xml version="1.0" encoding="ISO-8859-1" ?>'
                print '<agent_data agent_name="'+agent_name+'" description=""  timestamp="'+now+'" interval="300">'
                for module_name, module_data, module_is_incremental, module_units,  in modules:
                        print_module(module_name,module_data,is_incremental=module_is_incremental,units=module_units)
                print '</agent_data>'
        else:
                f = open(to_file,'w')
                f.write('<?xml version="1.0" encoding="ISO-8859-1" ?>\n')
                f.write('<agent_data agent_name="'+agent_name+'" description=""  timestamp="'+now+'" interval="300">\n')
                for module_name, module_data, module_is_incremental, module_units,  in modules:
                        print_module_to_file(module_name,module_data,f,is_incremental=module_is_incremental,units=module_units)
                f.write('</agent_data>')
                f.close()



running_container_list = subprocess.check_output(["docker", "ps", "-q"]).split()
stats = {}

for container_id in running_container_list:
        stats[container_id] = subprocess.check_output(["docker", "stats", "--no-stream=true", container_id])

for container_id,stat in stats.iteritems():
        stat = stat.split()
        modules = []
        modules.append(("CPU %",stat[14].split('%')[0],False,"%"))
        modules.append(("MEM %",stat[20].split('%')[0],False,"%"))
        modules.append(("Input traffic",stat[21].split('%')[0],True,stat[22]))
        modules.append(("Output traffic",stat[24].split('%')[0],True,stat[25]))

        print_agent_xml(container_id,modules,'/tmp/docker_plugin/'+container_id+'.'+str(int(time.time()))+'.data')

for xml in os.listdir('/tmp/docker_plugin'):
        subprocess.call([TENTACLE_CLIENT, "-a", SERVER_IP, "-p", "41121", "/tmp/docker_plugin/"+xml])
        move_file('/tmp/docker_plugin/'+xml,'/tmp/docker_plugin_sent/'+xml)

