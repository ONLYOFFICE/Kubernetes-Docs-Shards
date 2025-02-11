import os
import shutil
import logging
import time
import subprocess
from kubernetes import client

deployment_name = os.environ.get('DS_DEPLOYMENT_NAME')
productName = os.environ.get('PRODUCT_NAME')
cachePath = f'/var/lib/{productName}/documentserver/App_Data/cache/files/'
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
apps = client.AppsV1Api()


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setFormatter(logging.Formatter(formatter))
    stdout.setLevel(logging.DEBUG)
    logger.addHandler(stdout)
    logger.info('Running a script to clean up unused directories of previous DocumentServer versions in "cache/files"\n')


def get_ds_weight(replica):
    try:
        connect_count = ["/bin/bash", "-c", f"curl http://{replica}:8000/internal/connections/edit -s"]
        connect_count_process = subprocess.Popen(connect_count, stdout=subprocess.PIPE)
        connect_count_result = int(connect_count_process.communicate()[0])
        return connect_count_result
    except Exception as msg_get_connect_count:
        logger_pod_ds.error(
            'Failed when trying to get the number of connections... {}\n'.format(msg_get_connect_count))
        return None


def pod_deletion_cost(ep_ds):
    for ep_ip in ep_ds:
        try:
            replica = ep_ip.ip
            pod_name = ep_ip.target_ref.name
            weight = get_ds_weight(replica)
            if weight:
                patch = v1.patch_namespaced_pod(pod_name, ns, {"metadata": {"annotations": {"controller.kubernetes.io/pod-deletion-cost": str(weight)}}})
                logger_pod_ds.info(
                    f'The "pod-deletion-cost" annotation has been successfully added to the {pod_name}\n')
        except Exception as msg_patch_pod:
            logger_pod_ds.error(f'Error when adding an annotation to the Pod... {msg_patch_pod}')


def get_ds_ep():
    try:
        ep_list = v1.list_namespaced_endpoints(namespace=ns, field_selector=field_name)
        if ep_list.items[0].subsets:
            ep_ds = ep_list.items[0].subsets[0].addresses
            if not ep_ds:
                logger_pod_ds.warning(f'Empty "{ep_name}" endpoints list')
            else:
                pod_deletion_cost(ep_ds)
    except Exception as msg_get_ep:
        logger_pod_ds.error(f'Error when trying to search "{ep_name}" endpoints... {msg_get_ep}')


def get_ds_version():
    try:
        containers_list = apps.read_namespaced_deployment(name=deployment_name, namespace=ns)
        image = containers_list.spec.template.spec.containers[1].image
        tag = image.split(":")[1]
        if tag != '':
            return tag
        else:
            return 'none'
    except Exception as msg_read_tag:
        logger_pod_ds.error(f'Error reading the tag to the Pod... {msg_read_tag}')
        return 'none'


def clear_ds_folder_cache():
    try:
        ds_tag = get_ds_version()
        logger_pod_ds.info(f'The following DocumentServer tag is defined: {ds_tag}')
        if ds_tag != 'none':
            for file in os.listdir(cachePath):
                try:
                    if file != 'forgotten' and file != 'errors' and file != ds_tag:
                        if os.path.isdir(cachePath + file):
                            logger_pod_ds.info(f'The following directory will be deleted: {file}')
                            shutil.rmtree(cachePath + file)
                        else:
                            logger_pod_ds.info(f'The following file will be deleted: {file}')
                            os.remove(cachePath + file)
                except Exception as msg_delete_file:
                    logger_pod_ds.error(f'An error occurred when deleting "{file}"... {msg_delete_file}')
                    time.sleep(5)
        else:
            logger_pod_ds.error('The "DocumentServer" version is not defined... ')
            time.sleep(5)
    except Exception as msg_clear_dir:
        logger_pod_ds.error(f'Error when trying to clear directories of previous DocumentServer versions... {msg_clear_dir}')
        time.sleep(5)


init_logger('upgrade')
logger_pod_ds = logging.getLogger('upgrade.ds')
get_ds_ep()
clear_ds_folder_cache()
