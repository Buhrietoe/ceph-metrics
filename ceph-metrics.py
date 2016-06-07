#!/usr/bin/env python2

import glob
import json
import os
from rados import Rados
from rados import Error as RadosError
import timeout_decorator
from timeout_decorator import TimeoutError


CEPH_CLUSTER_CONFIGS = os.getenv('CEPH_CLUSTER_CONFIGS', '/etc/ceph/clusters/')
CLUSTER_COMMAND_TIMEOUT = int(os.getenv('CLUSTER_COMMAND_TIMEOUT', '15'))

def ceph_command(cluster, cmd):
    """
    Runs a ceph command and returns the results in a python dictionary
    """

    return_code, results, error = cluster.mon_command(
        json.dumps(dict(format='json', prefix=cmd)), '', timeout=30
    )

    if return_code != 0:
        sys.stderror.write("ceph command '%(cmd)s' failed with error %(error)s" % locals())
        sys.exit(1)

    return json.loads(results)


def get_ceph_clusters():
    """
    Grab dictionary of ceph clusters from the config directory specified in
    config.json
    """

    ceph_clusters = dict()
    for config_file in glob.glob(CEPH_CLUSTER_CONFIGS + '*.conf'):
        cluster_name = os.path.basename(os.path.splitext(config_file)[0])
        ceph_clusters[cluster_name] = dict()
        ceph_clusters[cluster_name]['conffile'] = CEPH_CLUSTER_CONFIGS + cluster_name + '.conf'
        ceph_clusters[cluster_name]['conf'] = dict(keyring = CEPH_CLUSTER_CONFIGS + cluster_name + '.keyring')

    return ceph_clusters

@timeout_decorator.timeout(CLUSTER_COMMAND_TIMEOUT)
def get_cluster_status(cluster_config):

    with Rados(**cluster_config) as cluster:
        return ceph_command(cluster, 'status')


def get_each_cluster_status(clusters):

    measurements = []
    for cluster_name, cluster in clusters.iteritems():
        cluster_status = {}
        try:
            cluster_status = get_cluster_status(cluster)
        except TimeoutError:
            cluster_status['health'] = dict(overall_status='TIMEOUT')

        measurements.append(status_to_measurement(cluster_status, cluster_name))

    return measurements


def status_to_measurement(status, cluster_name):

    name = 'ceph_status'
    tags = []
    values = []

    tags.append('cluster_name='+cluster_name)

    if status['health']['overall_status'] == 'HEALTH_OK':
        health = "1"
    else:
        health = "0"

    values.append('health='+health)

    if status['health']['overall_status'] != 'TIMEOUT':
        values.append('num_osds='+str(status['osdmap']['osdmap']['num_osds']))
        values.append('num_up_osds='+str(status['osdmap']['osdmap']['num_up_osds']))
        values.append('num_in_osds='+str(status['osdmap']['osdmap']['num_in_osds']))
        values.append('num_pgs='+str(status['pgmap']['num_pgs']))
        values.append('data_bytes='+str(status['pgmap']['data_bytes']))
        values.append('bytes_used='+str(status['pgmap']['bytes_used']))
        values.append('bytes_avail='+str(status['pgmap']['bytes_avail']))
        values.append('bytes_total='+str(status['pgmap']['bytes_total']))

    return dict(name=name, tags=tags, values=values)


def to_line_protocol(measurements):

    line_data = [measurement['name']+','+','.join(measurement['tags'])+' '+','.join(measurement['values']) for measurement in measurements]

    return "\n".join(line_data)


def main():

    clusters = get_ceph_clusters()

    stats = get_each_cluster_status(clusters)

    print to_line_protocol(stats)


if __name__ == "__main__":
    main()
