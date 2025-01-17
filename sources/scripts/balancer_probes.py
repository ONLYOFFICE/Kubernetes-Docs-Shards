import os
import logging
import sys
import subprocess
from kubernetes import client

label = os.environ["DS_POD_LABEL"]
ep_name = os.environ["DS_EP_NAME"]
field_name = f'metadata.name={ep_name}'

k8s_host = os.environ["KUBERNETES_SERVICE_HOST"]
api_server = f'https://{k8s_host}'
pathCrt = '/run/secrets/kubernetes.io/serviceaccount/ca.crt'
pathToken = '/run/secrets/kubernetes.io/serviceaccount/token'
pathNS = '/run/secrets/kubernetes.io/serviceaccount/namespace'

with open(pathToken, "r") as f_tok:
    token = f_tok.read()

with open(pathNS, "r") as f_ns:
    ns = f_ns.read()

configuration = client.Configuration()
configuration.ssl_ca_cert = pathCrt
configuration.host = api_server
configuration.verify_ssl = True
configuration.debug = False
configuration.api_key = {"authorization": "Bearer " + token}
client.Configuration.set_default(configuration)
v1 = client.CoreV1Api()


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setFormatter(logging.Formatter(formatter))
    stdout.setLevel(logging.DEBUG)
    logger.addHandler(stdout)


def get_pod_ds(pod_name):
    try:
        pod = v1.read_namespaced_pod(pod_name, ns)
    except Exception as msg_get_ep:
        logger_probes_balancer.error(f'Error when trying to get "{ep_name}" pod... {msg_get_ep}')
        sys.exit(1)


def list_pod_ds():
    try:
        pods = v1.list_namespaced_pod(namespace=ns, label_selector=label)
    except Exception as msg_get_ep:
        logger_probes_balancer.error(f'Error when trying to list "{ep_name}" pods... {msg_get_ep}')
        sys.exit(1)
    else:
        if pods.items:
            pod_name = pods.items[0].metadata.name
            get_pod_ds(pod_name)


def get_ep_status():
    try:
        ep = v1.list_namespaced_endpoints(namespace=ns, field_selector=field_name)
    except Exception as msg_get_ep:
        logger_probes_balancer.error(f'Error when trying to search "{ep_name}" endpoints... {msg_get_ep}')
        sys.exit(1)
    else:
        list_pod_ds()


def get_running_processes():
    proc1 = 'ds-ep-observer.py'
    proc2 = 'ds-pod-observer.py'
    proc3 = 'balancer-cm-observer.py'
    proc4 = 'nginx: worker process'
    proc5 = 'balancer-shutdown.py'
    try:
        processes_list = ["/bin/bash", "-c", "ps aux"]
        processes = subprocess.Popen(processes_list, stdout=subprocess.PIPE)
        processes_result = processes.communicate()[0].decode('utf-8')
    except Exception as msg_get_processes:
        logger_probes_balancer.error(f'Error when trying to list of running processes... {msg_get_processes}')
        sys.exit(1)
    else:
        if proc5 in processes_result:
            sys.exit()
        else:
            if proc1 in processes_result and proc2 in processes_result and proc3 in processes_result and proc4 in processes_result:
                get_ep_status()
            else:
                logger_probes_balancer.error('All necessary processes were not found in the list of running ones...')
                sys.exit(1)


init_logger('probes')
logger_probes_balancer = logging.getLogger('probes.balancer')
get_running_processes()
