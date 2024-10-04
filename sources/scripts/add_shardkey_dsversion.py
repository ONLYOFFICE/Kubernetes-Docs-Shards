import os
import sys
import logging
import time
import subprocess

redisConnectorName = os.environ.get('REDIS_CONNECTOR_NAME')
redisHost = os.environ.get('REDIS_SERVER_HOST')
redisPort = os.environ.get('REDIS_SERVER_PORT')
redisUser = os.environ.get('REDIS_SERVER_USER')
redisPassword = os.environ.get('REDIS_SERVER_PWD')
redisDBNumDSVersion = os.environ.get('REDIS_SERVER_DB_DS_VERSION')
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
shardDSVersion = ipShard + '-' + dsVersion


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
            db=redisDBNumDSVersion,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry_on_timeout=True
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error('Failed to check the availability of the Redis Standalone... {}\n'.format(msg_redis))
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
        logger_endpoints_ds.error('Failed to check the availability of the Redis Cluster... {}\n'.format(msg_redis))
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
            db=redisDBNumDSVersion,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry_on_timeout=True
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error('Failed to check the availability of the Redis Sentinel... {}\n'.format(msg_redis))
    else:
        logger_endpoints_ds.info('Successful connection to Redis Sentinel')
        return rc.ping()


def add_redis_key():
    if not rc.exists(shardDSVersion):
        try:
            rc.set(shardDSVersion, '0')
        except Exception as msg_check_redis:
            logger_endpoints_ds.error('Error when trying to write ShardKey with DS version to Redis... {}\n'.format(msg_check_redis))
        else:
            rc.close()
    else:
        rc.close()


def init_redis():
    logger_endpoints_ds.info('Checking Redis availability...')
    if redisConnectorName == 'redis' and not os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_status() is True:
            add_redis_key()
    elif redisConnectorName == 'redis' and os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_cluster_status() is True:
            add_redis_key()
    elif redisConnectorName == 'ioredis':
        if get_redis_sentinel_status() is True:
            add_redis_key()


def check_ds():
    while True:
        if not os.path.exists('/scripts/checkds.txt'):
            try:
                ds_status = ["/bin/bash", "-c", "curl -I -s http://localhost:8888/index.html | awk '/^HTTP/{print $2}'"]
                ds_status_process = subprocess.Popen(ds_status, stdout=subprocess.PIPE)
                ds_status_result = int(ds_status_process.communicate()[0])
                if ds_status_result == 200:
                    init_redis()
                    build_status = open('/scripts/checkds.txt', 'w')
                    build_status.write('Completed')
                    build_status.close()
                else:
                    time.sleep(1)
            except Exception as msg_ds_status:
                logger_endpoints_ds.error('Error when trying to get DS status... {}'. format(msg_ds_status))
                time.sleep(1)
        else:
            time.sleep(5)


init_logger('endpoints')
logger_endpoints_ds = logging.getLogger('endpoints.ds')
check_ds()
