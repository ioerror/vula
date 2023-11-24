import unittest

import schema

from vula.common import raw
from vula.organize import OrganizeState, SystemState

from .test_peer import desc, mkk


class TestOrganizeEngine(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 20000
        self.state = OrganizeState()
        # self.state.debug_log = lambda s: print(s)
        _ = self._assert_res_no_error(
            self.state.event_NEW_SYSTEM_STATE(
                SystemState(current_subnets={'10.0.0.0/24': ['10.0.0.9']})
            )
        )
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.local_domains', ['local'])
        )

    def _assert_res_no_error(self, result: {}):
        if result.error:
            self.assertEqual(result.error, ())
        return result

    def _assert_res_actions(self, result, actions):
        if actions != [a[0] for a in result.actions]:
            raise Exception(
                "Unexpected result: \n\nExpected: %r\n\n"
                "Got: %r\n\nFull result:\n%r"
                % (
                    actions,
                    ["%s (%s)" % (a[0], a[1]) for a in result.actions],
                    result,
                )
            )
        return result

    def _proc_desc(self, actions=[], error=False, **kw):
        result = self.state.event_INCOMING_DESCRIPTOR(desc(**kw))
        if result.error and not error:
            self.assertEqual(result.error, ())
        if actions:
            self._assert_res_actions(result, actions)
        return result

    def _add_alice_ok(self):
        return self._proc_desc(
            actions=['ACCEPT_NEW_PEER'],
            hostname='alice.local',
            vk=mkk('alicevk'),
            pk=mkk('alicepk'),
            addrs='10.0.0.1',
        )

    def _add_bob_maybe(
        self, hostname='bob.local', addrs='10.0.0.2', pk=mkk('bobpk')
    ):
        return self._proc_desc(
            hostname=hostname, vk=mkk('bobvk'), pk=pk, addrs=addrs
        )

    def _add_alice_bob_same_ip(self):
        self._add_alice_ok()
        return self._add_bob_maybe(addrs='10.0.0.1')

    def _add_alice_bob_same_pk(self):
        self._add_alice_ok()
        # bob is using alice's pk
        return self._add_bob_maybe(pk=mkk('alicepk'))

    def _add_alice_bob_same_ip_and_pk(self):
        self._add_alice_ok()
        # bob is using alice's pk *and* ip. the audacity.
        return self._add_bob_maybe(pk=mkk('alicepk'), addrs='10.0.0.1')

    def _add_alice_bob_same_ip_and_hostname(self):
        self._add_alice_ok()
        # now bobvk is claiming alice's name and ip. this is like the
        # real-world scenario where a user has changed their vk.
        return self._add_bob_maybe(hostname='alice.local', addrs='10.0.0.1')

    def test_add_replace_unpinned_ip(self):
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._assert_res_actions(
            self._add_alice_bob_same_ip(), ['REMOVE_PEER', 'ACCEPT_NEW_PEER']
        )
        self.assertEqual(
            self.state.peers.with_ip('10.0.0.1').name, 'bob.local'
        )

    def test_add_replace_unpinned_pk(self):
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._assert_res_actions(
            self._add_alice_bob_same_pk(), ['REMOVE_PEER', 'ACCEPT_NEW_PEER']
        )

    def test_add_replace_unpinned_ip_and_pk(self):
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._assert_res_actions(
            self._add_alice_bob_same_ip_and_pk(),
            ['REMOVE_PEER', 'ACCEPT_NEW_PEER'],
        )

    def test_add_replace_unpinned_ip_and_hostname(self):
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._assert_res_actions(
            self._add_alice_bob_same_ip_and_hostname(),
            ['REMOVE_PEER', 'ACCEPT_NEW_PEER'],
        )

    def test_pin_protected_same_ip(self):
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        )
        self.assertEqual(self.state.prefs.pin_new_peers, True)
        self._assert_res_actions(self._add_alice_bob_same_ip(), ['REJECT'])
        self.assertEqual(
            self.state.peers.with_ip('10.0.0.1').name, 'alice.local'
        )

    def test_pin_protected_same_pk(self):
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        )
        self.assertEqual(self.state.prefs.pin_new_peers, True)
        self._assert_res_actions(self._add_alice_bob_same_pk(), ['REJECT'])

    def test_pin_protected_same_ip_and_pk(self):
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        )
        self.assertEqual(self.state.prefs.pin_new_peers, True)
        self._assert_res_actions(
            self._add_alice_bob_same_ip_and_pk(), ['REJECT']
        )

    def test_pin_protected_same_ip_and_hostname(self):
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        )
        self.assertEqual(self.state.prefs.pin_new_peers, True)
        self._assert_res_actions(
            self._add_alice_bob_same_ip_and_hostname(), ['REJECT']
        )

    def test_pin_protected_disabled(self):
        """
        Pin protection doesn't apply to disabled peers.

        TODO: test that they can't be reenabled without removing the conflict
        """
        self._assert_res_no_error(
            self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        )
        self.assertEqual(self.state.prefs.pin_new_peers, True)
        self._add_alice_ok()
        self._assert_res_no_error(
            self.state.event_USER_EDIT(
                'SET',
                [
                    'peers',
                    self.state.peers.with_hostname('alice.local').id,
                    'enabled',
                ],
                False,
            )
        )
        self._assert_res_actions(
            self._add_bob_maybe(addrs='10.0.0.1'), ['ACCEPT_NEW_PEER']
        )
        self.assertEqual(
            self.state.peers.with_ip('10.0.0.1').name, 'bob.local'
        )

    def test_bogon_announcement(self):
        self._proc_desc(
            hostname='alice.local',
            vk=mkk(1),
            addrs='10.0.0.1',
            actions=['ACCEPT_NEW_PEER'],
        )
        self._proc_desc(
            hostname='mallory.local',
            vk=mkk('3'),
            addrs='10.0.2.1',
            actions=['REJECT'],
        )
        self.assertEqual(len(self.state.peers), 1)

    def test_update(self):
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._proc_desc(
            hostname='alice.local', vk=mkk(1), vf=1, addrs='10.0.0.1'
        )
        self._proc_desc(
            hostname='alice.local',
            vk=mkk(1),
            vf=2,
            addrs='10.0.0.1',
            actions=['UPDATE_PEER_DESCRIPTOR'],
        )
        self.assertEqual(self.state.peers[mkk(1)].descriptor.vf, 2)

    def test_replace_ip(self):
        "The one where Mallory takes the IP of unpinned peer Alice"
        self.assertEqual(self.state.prefs.pin_new_peers, False)
        self._proc_desc(
            hostname='alice.local',
            vk=mkk('alice'),
            pk=mkk('alicepk'),
            vf=1,
            addrs='10.0.0.1',
        )
        self._proc_desc(
            hostname='mallory.local',
            vk=mkk('mallory'),
            pk=mkk('mallorypk'),
            vf=1,
            addrs='10.0.0.1',
            actions=['REMOVE_PEER', 'ACCEPT_NEW_PEER'],
        )
        self.assertEqual(
            self.state.peers.with_ip('10.0.0.1').name, 'mallory.local'
        )
        with self.assertRaises(KeyError):
            self.state.peers.with_hostname('alice.local')

    def test_name_change_and_disable(self):
        s = self.state
        _ = self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        self.assertEqual(s.prefs.pin_new_peers, True)
        self._proc_desc(
            hostname='alice.local', vk=mkk('alice'), vf=1, addrs='10.0.0.1'
        )
        self._proc_desc(
            hostname='alice-1.local',
            vk=mkk('alice'),
            vf=2,
            addrs='10.0.0.1',
            actions=['UPDATE_PEER_DESCRIPTOR'],
        )
        self.assertEqual(
            s.peers.with_hostname('alice.local').name, 'alice-1.local'
        )
        self.assertEqual(
            s.peers.with_hostname('alice.local').nicknames,
            {'alice.local': True, 'alice-1.local': True},
        )
        self.assertEqual(
            s.peers.with_hostname('alice.local').enabled_names,
            ['alice-1.local', 'alice.local'],
        )
        self._assert_res_no_error(
            self.state.event_USER_EDIT(
                'SET',
                ['peers', mkk('alice'), 'nicknames', 'alice.local'],
                False,
            )
        )
        self.assertEqual(
            s.peers.with_ip('10.0.0.1').enabled_names,
            ['alice-1.local'],
        )

    def test_ignore_replay_unpinned(self):
        self._proc_desc(
            hostname='alice.local', vk=mkk(1), vf=2, addrs='10.0.0.2'
        )
        self._proc_desc(
            hostname='alice.local',
            vk=mkk(1),
            vf=1,
            addrs='10.0.0.1',
            actions=['IGNORE'],
        )
        self.assertEqual(
            raw(list(self.state.peers.with_hostname('alice.local').IPv4addrs)),
            ['10.0.0.2'],
        )

    def test_ignore_replay_pinned(self):
        _ = self.state.event_USER_EDIT('SET', 'prefs.pin_new_peers', True)
        self._proc_desc(
            hostname='alice.local', vk=mkk(1), vf=2, addrs='10.0.0.2'
        )
        self._proc_desc(
            hostname='alice.local',
            vk=mkk(1),
            vf=1,
            addrs='10.0.0.1',
            actions=['IGNORE'],
        )
        self.assertEqual(
            raw(list(self.state.peers.with_hostname('alice.local').IPv4addrs)),
            ['10.0.0.2'],
        )

    def test_state_validation(self):
        self._add_alice_ok()
        self._add_bob_maybe()
        # serialized dictionary of state:
        sd = self.state._dict()
        peers = self.state.peers  # shortcut
        # create bad state:
        sd['peers'][mkk('bobvk')]['petname'] = 'alice.local'
        with self.assertRaises(schema.SchemaError):
            # which means we're in an invalid state
            OrganizeState(sd)

        # make it valid again:
        sd['peers'][mkk('bobvk')]['petname'] = 'bob.local'
        OrganizeState(sd)
        # make it equal again:
        sd['peers'][mkk('bobvk')]['petname'] = ''
        self.assertEqual(
            OrganizeState(sd)._dict(),
            self.state._dict(),
        )
        # and then invalid due to an IP address conflict:
        sd['peers'][mkk("bobvk")]['IPv4addrs'].update(
            peers.with_hostname('alice.local')['IPv4addrs']
        )
        with self.assertRaises(schema.SchemaError):
            OrganizeState(sd)

        # make it valid again, by disabling a conflicting IP
        sd['peers'][peers.with_hostname('bob.local').id]['IPv4addrs'][
            list(peers.with_hostname('alice.local')['IPv4addrs'].keys())[0]
        ] = False
        OrganizeState(sd)

        # remove disabled IP to restore original state
        del sd['peers'][peers.with_hostname('bob.local').id]['IPv4addrs'][
            list(peers.with_hostname('alice.local')['IPv4addrs'].keys())[0]
        ]
        self.assertEqual(
            OrganizeState(sd)._dict(),
            self.state._dict(),
        )

        # create another invalid state,
        # where two peers are both set as the gateway
        sd['peers'][peers.with_hostname('alice.local').id][
            'use_as_gateway'
        ] = True
        sd['peers'][peers.with_hostname('bob.local').id][
            'use_as_gateway'
        ] = True
        with self.assertRaises(schema.SchemaError):
            OrganizeState(sd)

        # make it valid again
        sd['peers'][peers.with_hostname('bob.local').id][
            'use_as_gateway'
        ] = False
        OrganizeState(sd)

    def test_remove_nonlocal_unpinned(self):
        self._add_alice_ok()
        _ = self._assert_res_actions(
            self.state.event_NEW_SYSTEM_STATE(
                SystemState(self.state.system_state, current_subnets={})
            ),
            ['ADJUST_TO_NEW_SYSTEM_STATE', 'REMOVE_PEER'],
        )

    def test_user_edit_hostname_collision(self):
        self._add_alice_ok()
        self._assert_res_actions(
            self._add_bob_maybe(addrs='10.0.0.2'), ['ACCEPT_NEW_PEER']
        )
        res = self.state.event_USER_EDIT(
            'SET', ['peers', mkk('bobvk'), 'petname'], 'alice.local'
        )

        import packaging.version as pkgv
        import schema

        if pkgv.parse(schema.__version__) < pkgv.parse('0.7.3'):
            self.assertEqual(
                res.error.args[0], 'conflicting peers: {[peers].conflicts}'
            )
        else:
            self.assertEqual(
                res.error.args[0], 'conflicting peers: ' + mkk('alicevk')
            )


if __name__ == '__main__':
    unittest.main()
