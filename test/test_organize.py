import unittest
from pathlib import Path

import pytest

from unittest.mock import MagicMock, patch
from click.globals import push_context
from highctidh import ctidh

from vula.csidh import ctidh_parameters
from vula.organize import Organize


class TestOrganize(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path

    @patch("tkinter.Tk")
    @patch("vula.organize.Sys")
    @patch("vula.organize.ctidh", wraps=ctidh)
    def test_ctidh_dh_caching(
        self,
        mocked_ctidh: MagicMock,
        mocked_sys: MagicMock,
        mocked_tk: MagicMock,
    ) -> None:
        # Arrange
        keys_file = self.tmp_path.joinpath("keys.json")
        keys_file.touch()
        state_file = self.tmp_path.joinpath("state.json")
        state_file.touch()

        ctx = MagicMock()
        push_context(ctx)
        organize = Organize(
            ctx=ctx,
            keys_file=keys_file.as_posix(),
            state_file=state_file.as_posix(),
            interface=MagicMock(),
        )
        _ctidh = ctidh(ctidh_parameters)
        private_key_one = _ctidh.generate_secret_key()
        public_key_one = private_key_one.derive_public_key()
        private_key_two = _ctidh.generate_secret_key()
        public_key_two = private_key_two.derive_public_key()

        # Assert - initial state
        assert organize._ctidh_dh is None

        # Act - first call for key one
        result_one_first = organize.ctidh_dh(public_key_one)

        # Assert - active cache state
        assert organize._ctidh_dh is not None

        # Assert - cache miss
        mocked_ctidh.assert_called_once()
        mocked_ctidh.reset_mock()
        cache_info = organize._ctidh_dh.cache_info()
        assert cache_info.hits == 0
        assert cache_info.misses == 1

        # Act - second call for key one
        result_one_second = organize.ctidh_dh(public_key_one)

        # Assert - cache hit
        mocked_ctidh.assert_not_called()
        mocked_ctidh.reset_mock()
        cache_info = organize._ctidh_dh.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1

        # Assert - first and second result must be identical
        assert result_one_first == result_one_second

        # Act - new public key
        result_two = organize.ctidh_dh(public_key_two)

        # Assert - cache miss
        mocked_ctidh.assert_not_called()
        mocked_ctidh.reset_mock()
        cache_info = organize._ctidh_dh.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 2

        # Assert - result one and two must be different
        assert result_one_first != result_two

        # Act - third call for key one
        result_one_third = organize.ctidh_dh(public_key_one)

        # Assert - cache hit
        mocked_ctidh.assert_not_called()
        mocked_ctidh.reset_mock()
        cache_info = organize._ctidh_dh.cache_info()
        assert cache_info.hits == 2
        assert cache_info.misses == 2

        # Assert - first and second result must be identical
        assert result_one_first == result_one_third
