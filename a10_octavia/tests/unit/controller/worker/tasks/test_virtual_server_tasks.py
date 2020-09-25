#    Copyright 2020, A10 Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import imp
try:
    from unittest import mock
except ImportError:
    import mock

from oslo_config import cfg
from oslo_config import fixture as oslo_fixture

from octavia.common import data_models as o_data_models
from octavia.tests.common import constants as t_constants

from a10_octavia.common import config_options
from a10_octavia.common.data_models import VThunder
from a10_octavia.controller.worker.tasks import utils
import a10_octavia.controller.worker.tasks.virtual_server_tasks as task
from a10_octavia.tests.common import a10constants
from a10_octavia.tests.unit.base import BaseTaskTestCase

AMPHORA = o_data_models.Amphora(id=t_constants.MOCK_AMP_ID1)
VTHUNDER = VThunder()
VIP = o_data_models.Vip(ip_address=a10constants.MOCK_IP_ADDRESS)
LB = o_data_models.LoadBalancer(id=a10constants.MOCK_LOAD_BALANCER_ID, amphorae=[AMPHORA], vip=VIP)
VIP_META = utils.meta(LB, 'virtual_server', {})


class TestHandlerVirtualServerTasks(BaseTaskTestCase):

    def setUp(self):
        super(TestHandlerVirtualServerTasks, self).setUp()
        self.client_mock = mock.Mock()
        imp.reload(task)
        self.conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        self.conf.register_opts(config_options.A10_SLB_OPTS,
                                group=a10constants.SLB_CONF_SECTION)
        self.conf.register_opts(config_options.A10_GLOBAL_OPTS,
                                group=a10constants.A10_GLOBAL_CONF_SECTION)

    def tearDown(self):
        super(TestHandlerVirtualServerTasks, self).tearDown()
        self.conf.reset()

    def test_revert_create_virtual_server_task(self):
        mock_load_balancer = task.CreateVirtualServerTask()
        mock_load_balancer.axapi_client = self.client_mock
        mock_load_balancer.revert(LB, VTHUNDER)
        mock_load_balancer.axapi_client.slb.virtual_server.delete.assert_called_with(LB.id)

    def test_create_virtual_server_task(self):
        self.conf.config(group=a10constants.SLB_CONF_SECTION,
                         arp_disable=False)
        self.conf.config(group=a10constants.A10_GLOBAL_CONF_SECTION,
                         vrid=0)
        mock_load_balancer = task.CreateVirtualServerTask()
        mock_load_balancer.axapi_client = self.client_mock
        mock_load_balancer.CONF = self.conf
        mock_load_balancer.execute(LB, VTHUNDER)
        mock_load_balancer.axapi_client.slb.virtual_server.create.assert_called_with(LB.id,
                                                                                     LB.vip.ip_address,
                                                                                     arp_disable=False,
                                                                                     description=LB.description,
                                                                                     status=mock.ANY,
                                                                                     vrid=0,
                                                                                     axapi_body=VIP_META)

    def test_update_virtual_server_task(self):
        self.conf.config(group=a10constants.SLB_CONF_SECTION,
                         arp_disable=False)
        self.conf.config(group=a10constants.A10_GLOBAL_CONF_SECTION,
                         vrid=0)
        mock_load_balancer = task.UpdateVirtualServerTask()
        mock_load_balancer.axapi_client = self.client_mock
        mock_load_balancer.CONF = self.conf
        mock_load_balancer.execute(LB, VTHUNDER)
        mock_load_balancer.axapi_client.slb.virtual_server.update.assert_called_with(LB.id,
                                                                                     LB.vip.ip_address,
                                                                                     arp_disable=False,
                                                                                     description=LB.description,
                                                                                     status=mock.ANY,
                                                                                     vrid=0,
                                                                                     axapi_body=VIP_META)

    def test_delete_virtual_server_task(self):
        mock_load_balancer = task.DeleteVirtualServerTask()
        mock_load_balancer.axapi_client = self.client_mock
        mock_load_balancer.execute(LB, VTHUNDER)
        mock_load_balancer.axapi_client.slb.virtual_server.delete.assert_called_with(LB.id)
