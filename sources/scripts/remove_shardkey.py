import os
import sys
import subprocess
import logging
import time

redisConnectorName = os.environ.get('REDIS_CONNECTOR_NAME')
redisHost = os.environ.get('REDIS_SERVER_HOST')
redisPort = os.environ.get('REDIS_SERVER_PORT')
redisUser = os.environ.get('REDIS_SERVER_USER')
redisPassword = os.environ.get('REDIS_SERVER_PWD')
redisSentinelPassword = os.environ.get('REDIS_SENTINEL_PWD')
redisSentinelUsername = os.environ.get('REDIS_SENTINEL_USERNAME')
redisDBNum = os.environ.get('REDIS_SERVER_DB_KEYS_NUM')
redisConnectTimeout = 15
if os.environ.get('REDIS_CLUSTER_NODES'):
    redisClusterNodes = list(os.environ.get('REDIS_CLUSTER_NODES').split(" "))
    redisClusterNode = redisClusterNodes[0].split(":")[0]
    redisClusterPort = redisClusterNodes[0].split(":")[1]
if redisConnectorName == 'ioredis':
    redisSentinelGroupName = os.environ.get('REDIS_SENTINEL_GROUP_NAME')
    if os.environ.get('REDIS_SENTINEL_NODES'):
        redisSentinelNodes = list(os.environ.get('REDIS_SENTINEL_NODES').split(" "))
        redisSentinelNode = redisSentinelNodes[0].split(":")[0]
        redisSentinelPort = redisSentinelNodes[0].split(":")[1]

shardKey = os.environ.get('DEFAULT_SHARD_KEY')
epIP = os.environ.get('SHARD_IP')
epPort = os.environ.get('SHARD_PORT')
ipShard = epIP + ':' + epPort

grace_period = int(os.environ.get('TERMINATION_GRACE_PERIOD'))
grace_time = int(os.environ.get('TERMINATION_GRACE_TIME'))

total_result = {}


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setFormatter(logging.Formatter(formatter))
    stdout.setLevel(logging.DEBUG)
    logger.addHandler(stdout)
    logger.info('Running a script to shutdown the Shard and clear the keys belonging to it from Redis\n')


def get_redis_status():
    import redis
    from redis.retry import Retry
    from redis.backoff import ExponentialBackoff
    retry_strategy = Retry(ExponentialBackoff(), retries=3)
    global rc
    try:
        rc = redis.Redis(
            host=redisHost,
            port=redisPort,
            db=redisDBNum,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry=retry_strategy
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error('Failed to check the availability of the Redis Standalone... {}\n'.format(msg_redis))
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Standalone')
        return rc.ping()


def get_redis_cluster_status():
    from redis.cluster import RedisCluster as Redis
    from redis.cluster import ClusterNode
    from redis.retry import Retry
    from redis.backoff import ExponentialBackoff
    retry_strategy = Retry(ExponentialBackoff(), retries=3)
    global rc
    try:
        nodes = [ClusterNode(redisClusterNode, redisClusterPort)]
        rc = Redis(
            startup_nodes=nodes,
            username=redisUser,
            password=redisPassword,
            socket_connect_timeout=redisConnectTimeout,
            retry=retry_strategy
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error('Failed to check the availability of the Redis Cluster... {}\n'.format(msg_redis))
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Cluster')
        return rc.ping()


def get_redis_sentinel_status():
    import redis
    from redis import Sentinel
    from redis.retry import Retry
    from redis.backoff import ExponentialBackoff
    retry_strategy = Retry(ExponentialBackoff(), retries=3)
    global rc
    try:
        sentinel = Sentinel([(redisSentinelNode, redisSentinelPort)], socket_timeout=redisConnectTimeout, sentinel_kwargs={'password': redisSentinelPassword, 'username': redisSentinelUsername})
        master_host, master_port = sentinel.discover_master(redisSentinelGroupName)
        rc = redis.Redis(
            host=master_host,
            port=master_port,
            db=redisDBNum,
            password=redisPassword,
            username=redisUser,
            socket_connect_timeout=redisConnectTimeout,
            retry=retry_strategy
        )
        rc.ping()
    except Exception as msg_redis:
        logger_endpoints_ds.error('Failed to check the availability of the Redis Sentinel... {}\n'.format(msg_redis))
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_endpoints_ds.info('Successful connection to Redis Sentinel')
        return rc.ping()


def clear_shard_key():
    if rc.exists(ipShard):
        try:
            get_keys_shard = rc.get(ipShard).decode('utf-8')
            keys_shard = get_keys_shard.split()
            pipe = rc.pipeline()
            for key in keys_shard:
                pipe.delete(key)
            pipe.execute()
            rc.delete(ipShard)
        except Exception as msg_check_redis:
            logger_endpoints_ds.error('Error when trying to delete keys belonging to the {sk} shard from Redis... {em}\n'.format(sk=shardKey, em=msg_check_redis))
            total_result['CheckRedis'] = 'Failed'
        else:
            logger_endpoints_ds.info('Keys belonging to {} have been successfully deleted from Redis\n'.format(shardKey))
    else:
        logger_endpoints_ds.info('Endpoint shard {} was not found in Redis\n'.format(shardKey))
        rc.close()


def clear_redis():
    logger_endpoints_ds.info('Checking Redis availability...')
    if redisConnectorName == 'redis' and not os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_status() is True:
            clear_shard_key()
    elif redisConnectorName == 'redis' and os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_cluster_status() is True:
            clear_shard_key()
    elif redisConnectorName == 'ioredis':
        if get_redis_sentinel_status() is True:
            clear_shard_key()


def get_connect_count():
    try:
        connect_count = ["/bin/bash", "-c", "curl http://localhost:8000/internal/connections/edit -s"]
        connect_count_process = subprocess.Popen(connect_count, stdout=subprocess.PIPE)
        connect_count_result = int(connect_count_process.communicate()[0])
        total_result['GetConnectCount'] = 'Success'
        if connect_count_result == 0:
            return True
        else:
            return False
    except Exception as msg_get_connect_count:
        logger_endpoints_ds.error('Failed when trying to get the number of connections... {}\n'.format(msg_get_connect_count))
        total_result['GetConnectCount'] = 'Failed'
        return False


def shutdown_shard():
    try:
        shutdown_cmd = ["/bin/bash", "-c", "curl http://localhost:8000/internal/cluster/inactive -X PUT -s"]
        process = subprocess.Popen(shutdown_cmd, stdout=subprocess.PIPE)
        shutdown_result = process.communicate()[0].decode('utf-8')
    except Exception as msg_url:
        logger_endpoints_ds.error('Failed to check the availability of the DocumentServer... {}\n'.format(msg_url))
        total_result['ShutdownDS'] = 'Failed'
    else:
        if shutdown_result == "true":
            clear_redis()
            build_status = open('/scripts/results/status.txt', 'w')
            build_status.write('Completed')
            build_status.close()
        else:
            logger_endpoints_ds.error('The {} shard could not be disabled'.format(shardKey))
            sys.exit(1)


def prepare_for_shutdown_shard():
    current_grace_period = grace_period
    current_grace_time = grace_time
    while True:
        if get_connect_count() is True:
            shutdown_shard()
            break
        else:
            if current_grace_period < current_grace_time:
                shutdown_shard()
                break
            else:
                current_grace_period -= 1
                time.sleep(1)


def total_status():
    if 'Failed' in total_result.values():
        logger_endpoints_ds.error('Could not clear Redis of keys belonging to {}'.format(shardKey))
        sys.exit(1)


init_logger('endpoints')
logger_endpoints_ds = logging.getLogger('endpoints.ds')
prepare_for_shutdown_shard()
total_status()
