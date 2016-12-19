# -*- coding: utf8 -*-

import requests
from SpliceURL import Splice
from utils.public import logger


class BASE_SWARM_ENGINE_API:


    def __init__(self, port=2375, timeout=2):
        self.port      = port
        self.timeout   = timeout
        self.verify    = False

    def _checkSwarmToken(self, leader):
        """ 根据Leader查询集群令牌 """

        try:
            swarm = requests.get(Splice(netloc=leader, port=self.port, path='/swarm').geturl, timeout=self.timeout, verify=self.verify).json()
            token = swarm.get('JoinTokens')
        except Exception,e:
            logger.warn(e, exc_info=True)
        else:
            #dict, {u'Manager': u'xxx', u'Worker': u'xxx'}
            logger.info(token)
            return token

    def _checkSwarmLeader(self, swarm):
        """ 查询swarm集群Leader """

        if swarm:
            try:
                url  = Splice(netloc=swarm.get("manager")[0], port=self.port, path='/nodes').geturl
                data = requests.get(url, timeout=self.timeout, verify=self.verify).json()
                if isinstance(data, (list, tuple)):
                    leader = ( _.get('ManagerStatus', {}).get('Addr').split(':')[0] for _ in data if _.get('ManagerStatus', {}).get('Leader') ).next()
                else:
                    leader = None
                logger.info("get %s leader, request url is %s, response is %s, get leader is %s" %(swarm["name"], url, data, leader))
            except Exception,e:
                logger.warn(e, exc_info=True)
            else:
                return leader

    def _checkSwarmHealth(self, leader):
        """ 根据Leader查询某swarm集群是否健康 """

        state = []
        mnum  = 0
        logger.info("To determine whether the cluster is healthy, starting, swarm leader is %s" %leader)
        try:
            nodes = requests.get(Splice(netloc=leader, port=self.port, path='/nodes').geturl, timeout=self.timeout, verify=self.verify).json()
            logger.debug("check swarm health, swarm nodes length is %d" % len(nodes))
            for node in nodes:
                if node['Spec'].get('Role') == 'manager':
                    mnum += 1
                    isHealth = True if node['Status']['State'] == 'ready' and node['Spec'].get('Availability') == 'active' and node.get('ManagerStatus', {}).get('Reachability') == 'reachable' else False
                    if isHealth:
                        state.append(isHealth)
        except Exception,e:
            logger.warn(e, exc_info=True)
            return "ERROR"
        else:
            logger.info("To determine whether the cluster is healthy, ending, the state is %s, manager number is %d" %(state, mnum))
            if len(state) == mnum and state:
                return 'Healthy'
            else:
                return 'Unhealthy'

    def _checkSwarmNodeinfo(self, ip):
        """ 查询节点信息 """

        try:
            NodeUrl  = Splice(netloc=ip, port=self.port, path="/info").geturl
            NodeInfo = requests.get(NodeUrl, timeout=self.timeout, verify=self.verify).json()
        except Exception,e:
            logger.error(e, exc_info=True)
        else:
            logger.info("check node info, request url is %s ,response is %s" %(NodeUrl, NodeInfo))
            return NodeInfo

    def _checkSwarmNode(self, leader, node=None):
        """ 查询节点 """
        try:
            path     = "/nodes/" + node if node else "/nodes"
            NodeUrl  = Splice(netloc=leader, port=self.port, path=path).geturl
            NodeData = requests.get(NodeUrl, timeout=self.timeout, verify=self.verify).json()
        except Exception,e:
            logger.error(e, exc_info=True)
        else:
            logger.info("check node, request url is %s ,response is %s" %(NodeUrl, NodeData))
            return NodeData
