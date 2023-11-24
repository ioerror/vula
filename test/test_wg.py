from unittest import mock
from unittest.mock import Mock

from nacl.signing import SigningKey

import vula.wg
from vula.common import attrdict


class TestInterface:
    def test_sync_interface(self):
        """
        Try to sync a non existing interface when dryrun is set to True.
        """
        non_existent_interface = vula.wg.Interface("foo")
        key = SigningKey.generate()
        expected_result = [
            '# create interface',
            'ip link add foo type wireguard',
            '# bring up interface',
            'ip link set up foo',
            '# configure interface',
            "WireGuard.set('foo', **{'private_key': '<redacted private key>',"
            " 'listen_port': 9999, 'fwmark': 'foo'})",
        ]

        assert expected_result == non_existent_interface.sync_interface(
            key, 9999, "foo", True
        )

        """
        Try to sync a non existing interface when dryrun is set to False.
        """
        ipr_mock = Mock()
        ipr_mock.link_lookup.side_effect = [[], ['foo']]
        ipr_mock.get_links.return_value = False
        non_existent_interface._ipr = ipr_mock

        wg_mock = Mock()
        wg_mock.set.return_value = True
        non_existent_interface._wg = wg_mock

        query_mock = Mock()
        query_mock.return_value = True
        non_existent_interface.query = query_mock

        expected_result = [
            '# create interface',
            'ip link add foo type wireguard',
            '# bring up interface',
            'ip link set up foo',
            '# configure interface',
            "WireGuard.set('foo', **{'private_key': '<redacted private key>',"
            " 'listen_port': 9999, 'fwmark': 'bar'})",
        ]

        assert expected_result == non_existent_interface.sync_interface(
            key, 9999, "bar", False
        )
        ipr_mock.link.assert_has_calls(
            [
                mock.call('add', ifname='foo', kind='wireguard'),
                mock.call('set', index='foo', state='up'),
            ]
        )
        ipr_mock.get_links.assert_called_with(ifname='foo')

    def test_interface_query(self):
        """
        Ensure that a call to query() clears previously stored data
        """

        interface = vula.wg.Interface("foo")
        interface.update({'test': 'foo'})
        interface.query()
        assert interface == {}

        # Mock the `wg.info` inside the `query` method:
        wg_mock = Mock()
        wg_mock.info.return_value = [
            {'foo': 'bar', 'attrs': {'baz': 'test'}},
            't',
        ]
        interface._wg = wg_mock

        interface.query()

        assert interface == {'baz': 'test', 'peers': []}

        """
        Ensure that a call to query() populates Interface dict accordingly.
        """
        interface = vula.wg.Interface("vula")

        wgdevice_attrs = {
            'attrs': [
                (
                    'WGPEER_A_PUBLIC_KEY',
                    b'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3J' b'AOLXhFQ=',
                ),
                (
                    'WGPEER_A_PRESHARED_KEY',
                    b'ZGC6L/ZdYjtfwZuipT6rGHZ6AgHhHMTkg' b'bipmyK+Nag=',
                ),
                (
                    'WGPEER_A_LAST_HANDSHAKE_TIME',
                    {
                        'tv_sec': 1671376009,
                        'tv_nsec': 548272819,
                        'latest handshake': 'Sun Dec 18 15:06:49 2022',
                    },
                ),
                ('WGPEER_A_PERSISTENT_KEEPALIVE_INTERVAL', 0),
                ('WGPEER_A_TX_BYTES', 220),
                ('WGPEER_A_RX_BYTES', 308),
                ('WGPEER_A_PROTOCOL_VERSION', 1),
                (
                    'WGPEER_A_ENDPOINT',
                    {'family': 2, 'port': 5354, 'addr': '10.89.0.3'},
                ),
                (
                    'WGPEER_A_ALLOWEDIPS',
                    [
                        {
                            'attrs': [
                                ('WGALLOWEDIP_A_CIDR_MASK', 32),
                                ('WGALLOWEDIP_A_FAMILY', 2),
                                ('WGALLOWEDIP_A_IPADDR', '0a:59:00:03'),
                            ],
                            'addr': '10.89.0.3/32',
                        }
                    ],
                ),
            ]
        }

        mock_info_return_value = (
            {
                'cmd': 0,
                'version': 1,
                'reserved': 0,
                'attrs': [
                    ('WGDEVICE_A_LISTEN_PORT', 5354),
                    ('WGDEVICE_A_FWMARK', 555),
                    ('WGDEVICE_A_IFINDEX', 4),
                    ('WGDEVICE_A_IFNAME', 'vula'),
                    (
                        'WGDEVICE_A_PRIVATE_KEY',
                        b'MNQFqcSb6jXU2wbe+U1DIMBuYVTgyIXmUt7TffIWvWw=',
                    ),
                    (
                        'WGDEVICE_A_PUBLIC_KEY',
                        b'R55+QsNFggA7Z9s7iiRtGjkJsJVoj0G3mdimuL33/zQ=',
                    ),
                    ('WGDEVICE_A_PEERS', [wgdevice_attrs]),
                ],
                'header': {
                    'length': 320,
                    'type': 35,
                    'flags': 2,
                    'sequence_number': 255,
                    'pid': 195,
                    'error': None,
                    'target': 'localhost',
                },
            },
        )
        wg = Mock()
        wg.info.return_value = mock_info_return_value
        interface._wg = wg

        expected_result2 = {
            'listen_port': 5354,
            'fwmark': 555,
            'ifindex': 4,
            'ifname': 'vula',
            'private_key': b'MNQFqcSb6jXU2wbe+U1DIMBuYVTgyIXmUt7TffIWvWw=',
            'public_key': b'R55+QsNFggA7Z9s7iiRtGjkJsJVoj0G3mdimuL33/zQ=',
            'peers': [
                {
                    'remove': False,
                    'public_key': 'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLX'
                    'hFQ=',
                    'preshared_key': 'ZGC6L/ZdYjtfwZuipT6rGHZ6AgHhHMTkgbipm'
                    'yK+Nag=',
                    'allowed_ips': ['10.89.0.3/32'],
                    'endpoint_addr': '10.89.0.3',
                    'endpoint_port': 5354,
                    'persistent_keepalive': 0,
                    'stats': {
                        'rx_bytes': 308,
                        'tx_bytes': 220,
                        'latest_handshake': 1671376009,
                    },
                }
            ],
        }
        assert interface.query() == expected_result2

    def test_peers_by_pubkey(self):
        interface = vula.wg.Interface("vula")
        interface.update(popluated_interface())

        expected_result = {
            'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ=': {
                'remove': False,
                'public_key': 'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ=',
                'preshared_key': 'ZGC6L/ZdYjtfwZuipT6rGHZ6AgHhHMTkgbipmyK+N'
                'ag=',
                'allowed_ips': ['10.89.0.3/32'],
                'endpoint_addr': '10.89.0.3',
                'endpoint_port': 5354,
                'persistent_keepalive': 0,
                'stats': {
                    'rx_bytes': 308,
                    'tx_bytes': 220,
                    'latest_handshake': 1671376009,
                },
            }
        }
        assert interface._peers_by_pubkey == expected_result

    def test_apply_peerconfig(self):
        """
        Prepare a populated Interface with a mocked Wireguard property.
        """
        interface = vula.wg.Interface("vula")
        wg_mock = Mock()
        wg_mock.info.return_value = mock_wg_info_return()
        interface._wg = wg_mock
        existing_peer_pubkey = 'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ='

        """
        Try to update allowed_ips for an existing peer.
        """

        res = interface.apply_peerconfig(
            attrdict(
                public_key=existing_peer_pubkey,
                allowed_ips=['10.89.0.3/32', '10.89.0.5/32'],
            )
        )

        expected_result = (
            "# allowed_ips is ['10.89.0.3/32']; should be ['10."
            "89.0.3/32', '10.89.0.5/32']\n# reconfigure wiregua"
            "rd peer hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhF"
            "Q=\nvula wg set vula peer hDzSznlwlq9mk07QpNk+Acsf"
            "prrLg2DxSv3JAOLXhFQ= allowed-ips 10.89.0.3/32,10.8"
            "9.0.5/32 "
        )
        assert res == expected_result

        # Verify that Wireguard's `set` method is correctly called to update
        # the existing peer with the new value for allowed_ips.
        wg_mock.set.assert_called_with(
            'vula',
            peer=attrdict(
                public_key='hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ=',
                allowed_ips=['10.89.0.3/32', '10.89.0.5/32'],
            ),
        )

        """
        Try to remove a non-existent peer.
        """
        random_pubkey = "Rbt3m34X1PPIEd/LvW9G0tbImDfcQW0MyvGikM7ayio="
        res = interface.apply_peerconfig(
            attrdict(
                public_key=random_pubkey,
                remove=True,
            )
        )

        assert res == (
            f'# can\'t remove non-existent wireguard peer {random_pubkey}'
        )

        """
        Try to remove an existent peer.
        """

        res = interface.apply_peerconfig(
            attrdict(
                public_key=existing_peer_pubkey,
                remove=True,
            )
        )

        assert res == (
            f'# removing wireguard peer {existing_peer_pubkey}\n# reconfigure '
            f'wireguard peer {existing_peer_pubkey}\nvula wg set vula peer '
            f'{existing_peer_pubkey} remove '
        )

        # Verify that Wireguard's `set` method is correctly called to remove
        # the existing peer.
        wg_mock.set.assert_called_with(
            'vula',
            peer=attrdict(public_key=existing_peer_pubkey, remove=True),
        )


def popluated_interface():
    return {
        'listen_port': 5354,
        'fwmark': 555,
        'ifindex': 4,
        'ifname': 'vula',
        'private_key': b'MNQFqcSb6jXU2wbe+U1DIMBuYVTgyIXmUt7TffIWvWw=',
        'public_key': b'R55+QsNFggA7Z9s7iiRtGjkJsJVoj0G3mdimuL33/zQ=',
        'peers': [
            {
                'remove': False,
                'public_key': 'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ=',
                'preshared_key': 'ZGC6L/ZdYjtfwZuipT6rGHZ6AgHhHMTkgbipmyK+Nag'
                '=',
                'allowed_ips': ['10.89.0.3/32'],
                'endpoint_addr': '10.89.0.3',
                'endpoint_port': 5354,
                'persistent_keepalive': 0,
                'stats': {
                    'rx_bytes': 308,
                    'tx_bytes': 220,
                    'latest_handshake': 1671376009,
                },
            }
        ],
    }


# Use this simulated wireguard response to populate a vula interface with one
# peer with a public_key of: "hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOLXhFQ="
def mock_wg_info_return():
    return (
        {
            'cmd': 0,
            'version': 1,
            'reserved': 0,
            'attrs': [
                ('WGDEVICE_A_LISTEN_PORT', 5354),
                ('WGDEVICE_A_FWMARK', 555),
                ('WGDEVICE_A_IFINDEX', 4),
                ('WGDEVICE_A_IFNAME', 'vula'),
                (
                    'WGDEVICE_A_PRIVATE_KEY',
                    b'MNQFqcSb6jXU2wbe+U1DIMBuYVTgyIXmUt7TffIWvWw=',
                ),
                (
                    'WGDEVICE_A_PUBLIC_KEY',
                    b'R55+QsNFggA7Z9s7iiRtGjkJsJVoj0G3mdimuL33/zQ=',
                ),
                (
                    'WGDEVICE_A_PEERS',
                    [
                        {
                            'attrs': [
                                (
                                    'WGPEER_A_PUBLIC_KEY',
                                    b'hDzSznlwlq9mk07QpNk+AcsfprrLg2DxSv3JAOL'
                                    b'XhFQ=',
                                ),
                                (
                                    'WGPEER_A_PRESHARED_KEY',
                                    b'ZGC6L/ZdYjtfwZuipT6rGHZ6AgHhHMTkgbipmyK'
                                    b'+Nag=',
                                ),
                                (
                                    'WGPEER_A_LAST_HANDSHAKE_TIME',
                                    {
                                        'tv_sec': 1671376009,
                                        'tv_nsec': 548272819,
                                        'latest handshake': 'Sun Dec 18 15:06:'
                                        '49 2022',
                                    },
                                ),
                                ('WGPEER_A_PERSISTENT_KEEPALIVE_INTERVAL', 0),
                                ('WGPEER_A_TX_BYTES', 220),
                                ('WGPEER_A_RX_BYTES', 308),
                                ('WGPEER_A_PROTOCOL_VERSION', 1),
                                (
                                    'WGPEER_A_ENDPOINT',
                                    {
                                        'family': 2,
                                        'port': 5354,
                                        'addr': '10.89.0.3',
                                    },
                                ),
                                (
                                    'WGPEER_A_ALLOWEDIPS',
                                    [
                                        {
                                            'attrs': [
                                                (
                                                    'WGALLOWEDIP_A_CIDR_MASK',
                                                    32,
                                                ),
                                                ('WGALLOWEDIP_A_FAMILY', 2),
                                                (
                                                    'WGALLOWEDIP_A_IPADDR',
                                                    '0a:59:00:03',
                                                ),
                                            ],
                                            'addr': '10.89.0.3/32',
                                        }
                                    ],
                                ),
                            ]
                        }
                    ],
                ),
            ],
            'header': {
                'length': 320,
                'type': 35,
                'flags': 2,
                'sequence_number': 255,
                'pid': 195,
                'error': None,
                'target': 'localhost',
            },
        },
    )
