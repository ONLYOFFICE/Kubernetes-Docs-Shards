import os
import sys
import logging

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
ipShard = epIP + ':' + epPort

total_result = {}


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
        logger_test_ds.error(f'Failed to check the availability of the Redis Standalone... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Standalone')
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
        logger_test_ds.error(f'Failed to check the availability of the Redis Cluster... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Cluster')
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
        logger_test_ds.error(f'Failed to check the availability of the Redis Sentinel... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Sentinel')
        return rc.ping()


def add_redis_key():
    try:
        rc.set(shardKey, ipShard)
        rc.append(ipShard, f' {shardKey}')
        test_key = rc.get(shardKey).decode('utf-8')
        logger_test_ds.info(f'Shard Key Endpoint: {shardKey} = {test_key}')
    except Exception as msg_check_redis:
        logger_test_ds.error(f'Error when trying to write a ShardKey to Redis... {msg_check_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('The ShardKey was successfully recorded to Redis\n')
        rc.close()


def init_redis():
    logger_test_ds.info('Checking Redis availability...')
    if redisConnectorName == 'redis' and not os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_status() is True:
            add_redis_key()
    elif redisConnectorName == 'redis' and os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_cluster_status() is True:
            add_redis_key()
    elif redisConnectorName == 'ioredis':
        if get_redis_sentinel_status() is True:
            add_redis_key()


def total_status():
    if 'Failed' in total_result.values():
        logger_test_ds.error('Recording of "ShardKey" in Redis failed')
        sys.exit(1)


init_logger('test')
logger_test_ds = logging.getLogger('test.ds')
init_redis()
total_status()
