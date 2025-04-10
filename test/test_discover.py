from unittest.mock import MagicMock

from vula.constants import _TEST_DESC
from vula.peer import Descriptor
import vula.discover


class TestVulaServiceListener:
    def test_add_service_calls_callback(self):
        callback = MagicMock()
        zeroconf = MagicMock()
        zeroconf.get_service_info().properties = Descriptor.parse(
            _TEST_DESC
        ).as_zeroconf_properties
        listener = vula.discover.VulaServiceListener(callback)

        listener.add_service(zeroconf, "test_type", "test_name")

        callback.assert_called_once()

    def test_add_service_no_service_info(self):
        callback = MagicMock()
        zeroconf = MagicMock()
        zeroconf.get_service_info.return_value = None
        listener = vula.discover.VulaServiceListener(callback)

        listener.add_service(zeroconf, "test_type", "test_name")

        callback.assert_not_called()

    def test_add_service_invalid_descriptor(self):
        callback = MagicMock()
        props = {
            b'v4a': b'192.168.2.1',
            b'hostname': b'myhost',
            b'port': b'5054',
            b'dt': b'34',
            b'r': b'192.168.2.0/24',
            b'e': b'1',
        }
        zeroconf = MagicMock()
        zeroconf.get_service_info().properties = props
        listener = vula.discover.VulaServiceListener(callback)

        listener.add_service(zeroconf, "test_type", "test_name")

        callback.assert_not_called()

    def test_update_service_calls_add_service(self):
        listener = vula.discover.VulaServiceListener(MagicMock())
        listener.add_service = MagicMock()
        m = MagicMock()

        listener.update_service(m, "bar", "foo")

        listener.add_service.assert_called_once_with(m, "bar", "foo")


def alive_mock(x):
    m = MagicMock()
    m.is_alive.return_value = x
    return m


class TestDiscover:
    def test_callback_calls_all(self):
        a = MagicMock()
        b = MagicMock()
        c = MagicMock()

        discover = vula.discover.Discover()
        discover.callbacks = [a, b, c]

        discover.callback("foo")

        a.assert_called_once_with("foo")
        b.assert_called_once_with("foo")
        c.assert_called_once_with("foo")

    def test_is_not_alive(self):
        discover = vula.discover.Discover()
        discover.browsers = {
            '192.168.1.1': alive_mock(False),
            '192.168.1.2': alive_mock(False),
            '192.168.1.3': alive_mock(False),
        }

        alive = discover.is_alive()
        print(alive)
        assert alive is False

    def test_is_alive(self):
        discover = vula.discover.Discover()
        discover.browsers = {
            '192.168.1.1': alive_mock(False),
            '192.168.1.2': alive_mock(False),
            '192.168.1.3': alive_mock(True),
            '192.168.1.4': alive_mock(False),
        }

        alive = discover.is_alive()
        assert alive is True

    def test_shutdown_removes_browsers(self):
        discover = vula.discover.Discover()
        discover.browsers = {
            '192.168.1.1': MagicMock(),
            '192.168.1.2': MagicMock(),
            '192.168.1.3': MagicMock(),
        }

        discover.shutdown()

        assert discover.browsers == {}

    def test_shutdown_cancels_browsers(self):
        browser1 = MagicMock()
        browser2 = MagicMock()
        browser3 = MagicMock()
        discover = vula.discover.Discover()
        discover.browsers = {
            '192.168.1.1': browser1,
            '192.168.1.2': browser2,
            '192.168.1.3': browser3,
        }

        discover.shutdown()

        browser1.cancel.assert_called_once()
        browser2.cancel.assert_called_once()
        browser3.cancel.assert_called_once()
