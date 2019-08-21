from taskflow import task

from octavia.controller.worker import task_utils as task_utilities
from octavia.common import constants
import acos_client
from octavia.amphorae.driver_exceptions import exceptions as driver_except
import time
from oslo_log import log as logging
from oslo_config import cfg
from a10_octavia.common import openstack_mappings
from a10_octavia.controller.worker.tasks.policy import PolicyUtil
from a10_octavia.controller.worker.tasks import persist
from a10_octavia.controller.worker.tasks.common import BaseVThunderTask

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

class CreateVitualServerTask(BaseVThunderTask):
    """Task to create a virtual server in vthunder device."""

    def execute(self, loadbalancer_id, loadbalancer, vthunder):
        c = self.client_factory(vthunder)
        status = c.slb.UP
        if not loadbalancer.provisioning_status:
            status = c.slb.DOWN

        try:
            conf_templates = self.config.get('SLB','template-virtual-server')
            conf_templates = conf_templates.replace('"', '')
            virtual_server_templates = {}
            virtual_server_templates['template-server'] = conf_templates
        except:
            virtual_server_templates = None

        try:
            vip_meta = self.meta(loadbalancer, 'virtual_server', {})
            arp_disable=self.config.getboolean('SLB','arp_disable')
            vrid=self.config.getint('SLB','default_virtual_server_vrid')

            c = self.client_factory(vthunder)
            r = c.slb.virtual_server.create(loadbalancer_id, loadbalancer.vip.ip_address, arp_disable=arp_disable, status=status, vrid=vrid,
                                            virtual_server_templates=virtual_server_templates, axapi_body=vip_meta)

            status = { 'loadbalancers': [{"id": loadbalancer_id,
                       "provisioning_status": constants.ACTIVE }]}
            #LOG.info("vthunder details:" + str(vthunder))
        except Exception as e:
            r = str(e)
            LOG.info(r)
            status = { 'loadbalancers': [{"id": loadbalancer_id,
                       "provisioning_status": constants.ERROR }]}
        LOG.info(str(status))
        return status

    def revert(self, loadbalancer_id, *args, **kwargs):
        pass


class DeleteVitualServerTask(BaseVThunderTask):
    """Task to delete a virtual server in vthunder device."""

    def execute(self, loadbalancer, vthunder):
        loadbalancer_id = loadbalancer.id
        try:
            c = self.client_factory(vthunder)
            r = c.slb.virtual_server.delete(loadbalancer_id)
            status = { 'loadbalancers': [{"id": loadbalancer_id,
                       "provisioning_status": constants.DELETED }]}
        except Exception as e:
            r = str(e)
            LOG.info(r)
            status = { 'loadbalancers': [{"id": loadbalancer_id,
                       "provisioning_status": constants.ERROR }]}
        LOG.info(str(status))
        return status

    def revert(self, loadbalancer, *args, **kwargs):
        pass



