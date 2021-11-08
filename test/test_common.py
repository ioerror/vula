from unittest.mock import mock_open, patch

import pytest

import vula.common


class Testyamlfile:
    def test_from_yaml_file_nonexisting(self):
        with pytest.raises(FileNotFoundError):
            vula.common.yamlfile.from_yaml_file("non-existing-file.yml")

    def test_from_yaml_file(self):
        """
        Note: from_yaml_file uses click to open the file. Click 8.x uses
        builtins.open while click 7.x uses io.open, so we mock both here.
        """
        m = mock_open(read_data="bla:\n  foo: 2")
        with patch("builtins.open", m):
            with patch("io.open", m):
                print(vula.common.yamlfile)
                yaml = vula.common.yamlfile.from_yaml_file(
                    "some_yaml_file.yml"
                )
                assert yaml == {"bla": {"foo": 2}}
