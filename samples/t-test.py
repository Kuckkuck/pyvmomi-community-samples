#!/usr/bin/env python

from pyVmomi import vim, VmomiSupport
from prometheus_client import start_http_server, Summary, Counter, Gauge
from tools import cli
from pyVim.connect import SmartConnect, Disconnect
import atexit
import ssl
import datetime

def main():

    args = cli.get_args()

    # Start up the server to expose the prometheus metrics
    start_http_server(8000)

    # Connect to the host without SSL signing
    try:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=args.host,
             user=args.user,
             pwd=args.password,
             port=int(args.port),
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

    counterInfo = {}
    g = {}

    ##############################################################################
    # create a mapping from performance stats to their counterIDs
    # counterInfo: [performance stat => counterId]
    # performance stat example: cpu.usagemhz.LATEST
    # counterId example: 6
    print('Start perfManager.QueryPerfCounterByLevel: %s' % datetime.datetime.now())
    counterids=perfManager.QueryPerfCounterByLevel(level=4)
    print('Done perfManager.QueryPerfCounterByLevel: %s' % datetime.datetime.now())

    for c in counterids:
        fullName = c.groupInfo.key + "." + c.nameInfo.key + "." + c.rollupType
        print(fullName + ": " + str(c.key))
        counterInfo[fullName] = c.key

        # define a gauges for the counter ids
        g[fullName.replace('.','_')] = Gauge(fullName.replace('.','_'), fullName.replace('.','_'), ['vmware_name'])

#        print('QueryPerfCounterByLevel: Date now: %s' % datetime.datetime.now())
#        collected=[ 'cpu.usage.average', 'cpu.usagemhz.average', 'cpu.ready.summation', 'mem.usage.average', 'mem.swapinRate.average', 'mem.swapoutRate.average', 'mem.vmmemctl.average', 'mem.consumed.average', 'mem.overhead.average', 'disk.usage.average'  ]
    #    counterIDs = [counterInfo[k] for k in collected if k in counterInfo]
    counterIDs = [m.key for m in counterids]

    while True:

# REQUEST CreateContainerView
        print('Start content.viewManager.CreateContainerView: %s' % datetime.datetime.now())
        containerView = content.viewManager.CreateContainerView(container,
                                                            viewType,
                                                            recursive)
        print('Done content.viewManager.CreateContainerView: %s' % datetime.datetime.now())

        children = containerView.view
        count_vms=len(children)
        print("Number of VMs:" + str(count_vms))


    # REQUEST MetricId
    #    metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
    #                                                   instance="*")
    #                  for c in counterIDs]
    #    print('MetricId: Start: Date now: %s' % datetime.datetime.now())
    ########################################################################################
        # loop over all vmware machines
        for child in children:
            try:
                 # only consider machines which have an annotation and are powered on
                 if child.summary.config.annotation and child.summary.runtime.powerState=="poweredOn":
                    print("vm: " + child.summary.config.name)
                    # split the multi-line annotation into a dict per property (name, project-id, ...)
                    lis=child.summary.config.annotation.split('\n')
                    d = dict(s.rsplit(':',1) for s in filter(None, lis))

            # REQUEST MetricID
                    print('Start vim.PerformanceManager.MetricId: %s' % datetime.datetime.now())
                    metricIDs = [vim.PerformanceManager.MetricId(counterId=c,
                                                                 instance="*")
                                 for c in counterIDs]
                    print('Done vim.PerformanceManager.MetricId: %s' % datetime.datetime.now())

            #        print(metricIDs)
            # REQUEST QuerySpec - build query spec for the next metric query
                    print('Start vim.PerformanceManager.QuerySpec: %s' % datetime.datetime.now())
                    spec = vim.PerformanceManager.QuerySpec(maxSample=1,
                                                            entity=child,
                                                            metricId=metricIDs,
                                                            intervalId=20)
                    print('Done vim.PerformanceManager.QuerySpec: %s' % datetime.datetime.now())

            # REQUEST QueryStats - get metrics from vcenter
                    print('Start perfManager.QueryStats: %s' % datetime.datetime.now())
                    result = perfManager.QueryStats(querySpec=[spec])
                    print('Done perfManager.QueryStats: %s' % datetime.datetime.now())
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
            except VmomiSupport.ManagedObjectNotFound:
                    print('===> lost machine')

if __name__ == "__main__":
    main()
