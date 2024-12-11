import os
import shutil
import logging
import time
from kubernetes import client

deployment_name = os.environ.get('DS_DEPLOYMENT_NAME')
productName = os.environ.get('PRODUCT_NAME')
cachePath = f'/var/lib/{productName}/documentserver/App_Data/cache/files/'

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
v1 = client.AppsV1Api()


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setFormatter(logging.Formatter(formatter))
    stdout.setLevel(logging.DEBUG)
    logger.addHandler(stdout)
    logger.info('Running a script to clean up unused directories of previous DocumentServer versions in "cache/files"\n')


def get_ds_version():
    try:
        containers_list = v1.read_namespaced_deployment(name=deployment_name, namespace=ns)
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
clear_ds_folder_cache()
