import os
import sys
import logging
from kubernetes import client

redisConnectorName = os.environ.get('REDIS_CONNECTOR_NAME')
redisHost = os.environ.get('REDIS_SERVER_HOST')
redisPort = os.environ.get('REDIS_SERVER_PORT')
redisUser = os.environ.get('REDIS_SERVER_USER')
redisPassword = os.environ.get('REDIS_SERVER_PWD')
redisDBNum = os.environ.get('REDIS_SERVER_DB_KEYS_NUM')
redisConnectTimeout = 15
if os.environ.get('REDIS_CLUSTER_NODES'):
    redisClusterNodes = list(os.environ.get('REDIS_CLUSTER_NODES').split(" "))
    redisClusterNode = redisClusterNodes[0].split(":")[0]
    redisClusterPort = redisClusterNodes[0].split(":")[1]
if redisConnectorName == 'ioredis':
    redisSentinelGroupName = os.environ.get('REDIS_SENTINEL_GROUP_NAME')

shardKey = os.environ.get('DEFAULT_SHARD_KEY')
epIP = os.environ.get('SHARD_IP')
epPort = os.environ.get('SHARD_PORT')
dsVersion = os.environ.get('APP_VERSION') + '-' + os.environ.get('DS_VERSION_HASH')
ipShard = epIP + ':' + epPort
add_annotations = {"ds-ver-hash": dsVersion}

total_result = {}

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
    logger.info('Running the Redis initialization script with the "shardKey" value for the replica\n')


def get_redis_status():
    import redis
    global rc
    try:
        rc = redis.Redis(
            host=redisHost,
            port=redisPort,
            db=redisDBNum,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry_on_timeout=True
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error(f'Failed to check the availability of the Redis Standalone... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Standalone')
        return rc.ping()


def get_redis_cluster_status():
    from redis.cluster import RedisCluster as Redis
    from redis.cluster import ClusterNode
    global rc
    try:
        nodes = [ClusterNode(redisClusterNode, redisClusterPort)]
        rc = Redis(
            startup_nodes=nodes,
            username=redisUser,
            password=redisPassword,
            socket_connect_timeout=redisConnectTimeout,
            retry_on_timeout=True
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error(f'Failed to check the availability of the Redis Cluster... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Cluster')
        return rc.ping()


def get_redis_sentinel_status():
    import redis
    from redis import Sentinel
    global rc
    try:
        sentinel = Sentinel([(redisHost, redisPort)], socket_timeout=redisConnectTimeout)
        master_host, master_port = sentinel.discover_master(redisSentinelGroupName)
        rc = redis.Redis(
            host=master_host,
            port=master_port,
            db=redisDBNum,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry_on_timeout=True
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error(f'Failed to check the availability of the Redis Sentinel... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Sentinel')
        return rc.ping()


def add_redis_key():
    try:
        rc.set(shardKey, ipShard)
        rc.append(ipShard, f' {shardKey}')
        test_key = rc.get(shardKey).decode('utf-8')
    except Exception as msg_check_redis:
        logger_endpoints_ds.error(f'Error when trying to write a ShardKey to Redis... {msg_check_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info(f'ShardKey {shardKey} = {test_key} was successfully recorded to Redis\n')
        rc.close()


def patch_pod():
    try:
        patch = v1.patch_namespaced_pod(shardKey, ns, {"metadata": {"annotations": add_annotations}})
    except Exception as msg_patch_pod:
        logger_endpoints_ds.error(f'Error when adding an annotation to the Pod... {msg_patch_pod}')
        total_result['PatchPod'] = 'Failed'
    else:
        logger_endpoints_ds.info(f'The {add_annotations} annotation has been successfully added to the Pod\n')


def init_redis():
    logger_endpoints_ds.info('Checking Redis availability...')
    if redisConnectorName == 'redis' and not os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_status() is True:
            add_redis_key()
            patch_pod()
    elif redisConnectorName == 'redis' and os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_cluster_status() is True:
            add_redis_key()
            patch_pod()
    elif redisConnectorName == 'ioredis':
        if get_redis_sentinel_status() is True:
            add_redis_key()
            patch_pod()


def total_status():
    if 'Failed' in total_result.values():
        logger_endpoints_ds.error('Recording of "ShardKey" in Redis failed')
        sys.exit(1)


init_logger('endpoints')
logger_endpoints_ds = logging.getLogger('endpoints.ds')
init_redis()
total_status()
