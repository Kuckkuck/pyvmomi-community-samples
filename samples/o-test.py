#!/usr/bin/env python

from pyVmomi import vim
from prometheus_client import start_http_server, Summary, Counter, Gauge
from tools import cli
from pyVim.connect import SmartConnect, Disconnect
import atexit
import ssl
import datetime
from yamlconfig import YamlConfig
import argparse

defaults = {
            'vcenter_ip': 'localhost',
            'vcenter_user': 'administrator@vsphere.local',
            'vcenter_password': 'password',
            'ignore_ssl': True
            }

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                    help="Specify config file", metavar="FILE")
    args, remaining_argv = parser.parse_known_args()
    config = YamlConfig(args.config, defaults)

    # Start up the server to expose the prometheus metrics
    start_http_server(8000)

    # Connect to the host without SSL signing
    si=None
    context = None
    if config['main']['ignore_ssl'] and \
       hasattr(ssl, "_create_unverified_context"):
       context = ssl._create_unverified_context()

    try:
        si = SmartConnect(host=config['main']['host'],
             user=config['main']['user'],
             pwd=config['main']['password'],
             port=int(config['main']['port']),
             sslContext=context)
        atexit.register(Disconnect, si)

    except IOError as e:
        pass

    if not si:
        raise SystemExit("Unable to connect to host with supplied info.")

    content = si.RetrieveContent()
    perfManager = content.perfManager


##############################################################################
    # create a list of vim.VirtualMachine objects so that we can query them for statistics
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True

# REQUEST CreateContainerView
    containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)

    children = containerView.view
    count_vms=len(children)
    print("Count of VMs:" + str(count_vms))
    print('CreateContainerView: Start: Date now: %s' % datetime.datetime.now())

##############################################################################
    # create a mapping from performance stats to their counterIDs
    # counterInfo: [performance stat => counterId]
    # performance stat example: cpu.usagemhz.LATEST
    # counterId example: 6
    print('Start: Date now: %s' % datetime.datetime.now())
    counterInfo = {}
    counterids=perfManager.QueryPerfCounterByLevel(level=4)

    g = {}
    for c in counterids:
        fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
        print(fullName + ": " + str(c.key))
        counterInfo[fullName] = c.key

        # define a gauges for the counter ids
        g[fullName.replace('.','_')] = Gauge(fullName.replace('.','_'), fullName.replace('.','_'), ['vmware_name'])

    print('QueryPerfCounterByLevel: Date now: %s' % datetime.datetime.now())
    collected=config['main']['vm_metrics']
    counterIDs = [counterInfo[k] for k in collected if k in counterInfo]
#    counterIDs = [m.key for m in counterids]

# REQUEST MetricId
#    metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
#                                                   instance="*")
#                  for c in counterIDs]
#    print('MetricId: Start: Date now: %s' % datetime.datetime.now())
########################################################################################
    # loop over all vmware machines
    for child in children:
     # only consider machines which have an annotation and are powered on
     if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
        # split the multi-line annotation into a dict per property (name, project-id, ...)
        lis=child.summary.config.annotation.split('\n')
        d = dict(s.rsplit(':',1) for s in filter(None, lis))

# REQUEST MetricID
        metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
                                                     instance="*")
                     for c in counterIDs]
        print('MetricId: Start: Date now: %s' % datetime.datetime.now())

#        print(metricIDs)
# REQUEST QuerySpec - build query spec for the next metric query
        spec = vim.PerformanceManager.QuerySpec(maxSample=1,
                                                entity=child,
                                                metricId=metricIDs,
                                                intervalId=20)

        print('QuerySpec: Start: Date now: %s' % datetime.datetime.now())
# REQUEST QueryStats - get metrics from vcenter
        result = perfManager.QueryStats(querySpec=[spec])
        print('QueryStats: Start: Date now: %s' % datetime.datetime.now())
        # Loop through the results and print the output
        output = ""
        for r in result:
#            if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
            # loop over the metrics
            for val in result[0].value:
                 if val:
                     # print vmware name
#                     output += "id:" + child.summary.config.name + ","
                     # print key names
#                     output += counterInfo.keys()[counterInfo.values().index(val.id.counterId)]
                     # print key values plus metadata
#                     output += ": " + str(val.value[0]) + ", name:" + d['name'] + ", project_id:" + d['projectid'] + "\n"
#               output += "\n"
                     # try to remove empty lines (maybe does not seem to work)
#                     print(filter(None, output))
#        if counterInfo.keys()[counterInfo.values().index(val.id.counterId)] == 'cpu.usage.average':
                # send metrics to prometheus exporter
                     g[counterInfo.keys()[counterInfo.values().index(val.id.counterId)].replace('.','_')].labels(d['name']).set(val.value[0])

if __name__ == "__main__":
    main()
