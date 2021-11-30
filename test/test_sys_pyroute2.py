import time
from unittest.mock import MagicMock, patch

import vula.sys_pyroute2


class TestSys:
    def test_start_stop_monitor(self):
        mock_organize = MagicMock()
        with patch("vula.sys_pyroute2.IPRSocket") as mock_ipr, patch(
            "vula.sys_pyroute2.WgInterface"
        ):
            mock_ipr.return_value.get.return_value = [
                {"event": "NON_EXISTING"}
            ]
            sys = vula.sys_pyroute2.Sys(mock_organize)

            sys.start_monitor()
            sys.stop_monitor()
            # HACK to force monitor_thread to run
            time.sleep(0.1)

            mock_organize.log.info.assert_called_once_with(
                "Stopping netlink monitor thread"
            )
            mock_ipr.return_value.close.assert_called_once()

    def test_monitor_newneigh(self):
        mock_organize = MagicMock()
        with patch("vula.sys_pyroute2.IPRSocket") as mock_ipr, patch(
            "vula.sys_pyroute2.WgInterface"
        ):
            mock_ipr.return_value.get.return_value = [
                {"event": "RTM_NEWNEIGH"}
            ]
            sys = vula.sys_pyroute2.Sys(mock_organize)
            sys.get_new_system_state = MagicMock()
            sys._stop_monitor = True

            sys._monitor()

            sys.get_new_system_state.assert_not_called()

    def test_monitor_netlink_msg(self):
        mock_organize = MagicMock()
        with patch("vula.sys_pyroute2.IPRSocket") as mock_ipr, patch(
            "vula.sys_pyroute2.WgInterface"
        ):
            mock_ipr.return_value.get.return_value = [{"event": "RTM_NEWADDR"}]
            sys = vula.sys_pyroute2.Sys(mock_organize)
            sys.get_new_system_state = MagicMock()
            sys._stop_monitor = True

            sys._monitor()

            sys.get_new_system_state.assert_called_once()

    def test_monitor_bug(self):
        mock_organize = MagicMock()
        with patch("vula.sys_pyroute2.IPRSocket") as mock_ipr, patch(
            "vula.sys_pyroute2.WgInterface"
        ):
            mock_ipr.return_value.get.side_effect = [
                [],
                [{"event": "NON_EXISTING"}],
            ]
            sys = vula.sys_pyroute2.Sys(mock_organize)
            sys.get_new_system_state = MagicMock()
            sys._stop_monitor = True

            sys._monitor()

            sys.get_new_system_state.assert_not_called()
            assert mock_organize.log.info.call_count == 2
