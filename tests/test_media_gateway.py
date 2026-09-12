import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import docker
from services.install_state import InstallState
from services.media_gateway import MediaGateway, NAME, LABEL, domain


class MediaGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = MagicMock()
        self.gateway = MediaGateway(self.manager, InstallState(Path(self.temp.name)))
        self.app = MagicMock()
        self.app.attrs = {'NetworkSettings':{'Ports':{'8080/tcp':[{'HostIp':'0.0.0.0','HostPort':'8097'}]}}}

    def tearDown(self):
        self.temp.cleanup()

    def test_domain_input_cannot_inject_config(self):
        self.assertEqual(domain('https://Media.example.com/'),'media.example.com')
        for value in ('localhost','https://example.com/x','http://example.com','example.com:443','x.example.com\n{','https://u:p@example.com','127.0.0.1'):
            with self.assertRaises(ValueError): domain(value)

    def test_reuse_owned_gateway(self):
        client=self.manager.client
        own=client.containers.get.return_value
        own.labels={LABEL:'1','dk.fjordhub.media-domain':'media.example.com'}
        own.status='running';own.exec_run.return_value.exit_code=0
        client.containers.list.return_value=[own]
        self.gateway.ensure_gateway(client,self.app,'media.example.com')
        client.containers.create.assert_not_called()
        client.images.pull.assert_not_called()
        own.exec_run.assert_called_once()

    def test_other_gateway_and_occupied_ports_are_untouched(self):
        client=self.manager.client
        client.containers.get.return_value.labels={}
        with self.assertRaisesRegex(RuntimeError,'anden container'):
            self.gateway.ensure_gateway(client,self.app,'media.example.com')
        client.containers.get.side_effect=docker.errors.NotFound('missing')
        other=MagicMock();other.name='existing-proxy';other.attrs={'NetworkSettings':{'Ports':{'443/tcp':[{'HostPort':'443','HostIp':'0.0.0.0'}]}}}
        client.containers.list.return_value=[other]
        with self.assertRaisesRegex(RuntimeError,r'existing-proxy: 0\.0\.0\.0:443'):
            self.gateway.ensure_gateway(client,self.app,'media.example.com')
        client.containers.create.assert_not_called()
        other.stop.assert_not_called()

    def test_udp_port_does_not_block_tcp_gateway(self):
        client=self.manager.client
        own=client.containers.get.return_value
        own.labels={LABEL:'1','dk.fjordhub.media-domain':'media.example.com'}
        own.status='running';own.exec_run.return_value.exit_code=0
        other=MagicMock();other.id='other'
        other.attrs={'NetworkSettings':{'Ports':{'443/udp':[{'HostPort':'443'}]}}}
        client.containers.list.return_value=[other]
        self.gateway.ensure_gateway(client,self.app,'media.example.com')
        own.exec_run.assert_called_once()

    def test_failed_https_never_activates(self):
        self.gateway.lock.acquire()
        with patch('services.media_gateway.flix',return_value={'media_url':'','web_url':''}) as flix, patch.object(self.gateway,'verify',side_effect=RuntimeError('TLS failed')):
            self.gateway.run({'container_name':'fjordflix'},'media.example.com','https://film.example.com','existing')
            self.assertNotIn('activate',[c.args[1] for c in flix.call_args_list])
            self.assertEqual(self.gateway.status()['error'],'TLS failed')
            self.assertFalse(self.gateway.status()['running'])

    def test_existing_proxy_only_activates_after_proof(self):
        self.gateway.lock.acquire()
        with patch('services.media_gateway.flix',return_value={'media_url':'','web_url':''}) as flix, patch.object(self.gateway,'verify') as verify:
            self.gateway.run({'container_name':'fjordflix'},'media.example.com','https://film.example.com','existing')
            verify.assert_called_once()
            self.assertEqual(flix.call_args_list[-1].args[1],'activate')
            self.manager.client.containers.create.assert_not_called()
            self.assertTrue(self.gateway.status()['active'])

    def test_cloudflare_proxy_is_rejected(self):
        with patch('services.media_gateway.requests.Session') as factory:
            response=factory.return_value.__enter__.return_value.get.return_value
            response.headers={'cf-ray':'test'}
            with self.assertRaisesRegex(RuntimeError,'DNS only'):
                self.gateway.verify('media.example.com','nonce')
