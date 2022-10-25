import json
from unittest.mock import MagicMock, Mock, patch

import vula.verify


class TestVerifyCommands:
    def create_verify_commands(self):
        test_descriptor = {
            '192.168.122.140': {
                'r': '',
                'pk': 'Y' * 43 + '=',
                'c': 'Z' * 86 + '==',
                'addrs': '192.168.122.140',
                'vk': 'A' * 43 + '=',
                'vf': '1638114786',
                'dt': '86400',
                'port': '5354',
                'hostname': 'aula.local.',
                'e': 'False',
                's': 'X' * 86 + '==',
            },
            '192.168.122.150': {
                'r': '',
                'pk': 'G' * 43 + '=',
                'c': 'H' * 86 + '==',
                'addrs': '192.168.122.150',
                'vk': 'A' * 43 + '=',
                'vf': '1638114786',
                'dt': '86400',
                'port': '5354',
                'hostname': 'aula.local.',
                'e': 'False',
                's': 'X' * 86 + '==',
            },
        }

        mockdbus = Mock()
        mockpeer = Mock()
        mockpeer.our_latest_descriptors.return_value = json.dumps(
            test_descriptor
        )
        mockdbus.SystemBus.return_value.get.return_value = mockpeer

        mockclickctx = MagicMock()
        mockclickctx.meta.get.return_value.get.return_value = None

        assert (
            mockdbus.SystemBus().get().our_latest_descriptors()
            == json.dumps(test_descriptor)
        )

        with patch("vula.verify.pydbus", mockdbus):
            # the __wrapped__ call gets rid of the click decorators.
            verify = vula.verify.VerifyCommands.__wrapped__(mockclickctx)

        return verify

    def test_init_loads_descriptors(self):
        verify = self.create_verify_commands()
        assert verify.vk is not None
        assert verify.my_descriptors is not None

    def test_my_vk(self, capsys):
        verify = self.create_verify_commands()

        verify.my_vk()
        output = capsys.readouterr().out
        assert 'A' * 43 + '=' in output
        assert 'Y' * 43 + '=' not in output
        assert 'X' * 86 + '=' not in output
        assert 'Z' * 86 + '=' not in output

    def test_my_descriptor(self, capsys):
        verify = self.create_verify_commands()
        verify.my_descriptor()
        output = capsys.readouterr().out
        assert 'Descriptor for 192.168.122.140:' in output
        assert 'Descriptor for 192.168.122.150' in output
