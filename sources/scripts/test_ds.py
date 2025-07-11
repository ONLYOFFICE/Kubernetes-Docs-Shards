import os
import sys
import subprocess
import time
import logging

url = 'http://docservice:8000/healthcheck'

redisConnectorName = os.environ.get('REDIS_CONNECTOR_NAME')
redisHost = os.environ.get('REDIS_SERVER_HOST')
redisPort = os.environ.get('REDIS_SERVER_PORT')
redisUser = os.environ.get('REDIS_SERVER_USER')
redisPassword = os.environ.get('REDIS_SERVER_PWD')
redisSentinelPassword = os.environ.get('REDIS_SENTINEL_PWD')
redisSentinelUsername = os.environ.get('REDIS_SENTINEL_USERNAME')
redisDBNum = os.environ.get('REDIS_SERVER_DB_NUM')
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

total_result = {}


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setFormatter(logging.Formatter(formatter))
    stdout.setLevel(logging.DEBUG)
    logger.addHandler(stdout)
    logger.info('Running a script to test the availability of DocumentServer and dependencies\n')


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
        logger_test_ds.error(f'Failed to check the availability of the Redis Standalone... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Standalone')
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
        logger_test_ds.error(f'Failed to check the availability of the Redis Cluster... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Cluster')
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
        logger_test_ds.error(f'Failed to check the availability of the Redis Sentinel... {msg_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        logger_test_ds.info('Successful connection to Redis Sentinel')
        return rc.ping()


def check_redis_key():
    try:
        rc.set('testDocsServer', 'ok')
        test_key = rc.get('testDocsServer').decode('utf-8')
        logger_test_ds.info(f'Test Key: {test_key}')
    except Exception as msg_check_redis:
        logger_test_ds.error(f'Error when trying to write a key to Redis... {msg_check_redis}\n')
        total_result['CheckRedis'] = 'Failed'
    else:
        rc.delete('testDocsServer')
        logger_test_ds.info('The test key was successfully recorded and deleted from Redis\n')
        rc.close()
        total_result['CheckRedis'] = 'Success'


def check_redis():
    logger_test_ds.info('Checking Redis availability...')
    if redisConnectorName == 'redis' and not os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_status() is True:
            check_redis_key()
    elif redisConnectorName == 'redis' and os.environ.get('REDIS_CLUSTER_NODES'):
        if get_redis_cluster_status() is True:
            check_redis_key()
    elif redisConnectorName == 'ioredis':
        if get_redis_sentinel_status() is True:
            check_redis_key()


def get_ds_status():
    import requests
    from requests.adapters import HTTPAdapter
    logger_test_ds.info('Checking DocumentServer availability...')
    ds_adapter = HTTPAdapter(max_retries=3)
    ds_session = requests.Session()
    ds_session.mount(url, ds_adapter)
    try:
        response = ds_session.get(url, timeout=15)
    except Exception as msg_url:
        logger_test_ds.error(f'Failed to check the availability of the DocumentServer... {msg_url}\n')
        total_result['CheckDS'] = 'Failed'
    else:
        logger_test_ds.info(f'The DocumentServer is available: {response.text}\n')
        if response.text == 'true':
            total_result['CheckDS'] = 'Success'
        else:
            total_result['CheckDS'] = 'Failed'


def total_status():
    logger_test_ds.info('As a result of the check, the following results were obtained:')
    for key, value in total_result.items():
        logger_test_ds.info(f'{key} = {value}')
    if total_result['CheckDS'] != 'Success':
        sys.exit(1)


init_logger('test')
logger_test_ds = logging.getLogger('test.ds')
check_redis()
get_ds_status()
total_status()
