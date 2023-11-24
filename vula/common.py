"""
*vula* common functions.
"""
from __future__ import annotations

import copy
import json
import os
import pdb
import re
from base64 import b64decode, b64encode
from ipaddress import ip_address, ip_network
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, Optional

import click
import pydbus
import yaml
from schema import And, Or, Schema, SchemaError, Use

from .constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
from .notclick import DualUse, Exit  # noqa: F401

try:
    import pygments
    from pygments import formatters, lexers  # noqa: F401
except ImportError:
    pygments = None

bp = pdb.set_trace

memoize = lambda f: (
    lambda d={}: lambda *a: d.setdefault(a, a in d or f(*a))
)()


def chown_like_dir_if_root(path):
    """
    This chowns a file to have the same owner as its parent, if we are running
    as root. Otherwise, it does nothing.

    Normally vula is not run as root. The purpose of this function is to ensure
    that files remain owned by their correct user (which is hopefully the owner
    of the directory they reside in) if/when vula *is* run is root.

    As of this writing, this function is only used by the organize daemon when
    writing the hosts file.

    FIXME: this should probably be used when writing the state file as well?
    """
    if os.getuid() == 0:
        dirstat = os.stat(os.path.dirname(os.path.realpath(path)))
        os.chown(path, dirstat.st_uid, dirstat.st_gid)


def _safer_load(
    yaml_file: str,
    schema: Schema,
    size_constraint_min: int = 0,
    size_constraint_max: int = 65000,
) -> Optional[Dict]:
    """
    *_safer_load* loads opens *yaml_file* and validates it based on a defined
    *schema* and ensures it is not smaller than *size_constraint_min* and not
    larger than *size_constraint_max*.
    """
    log: Logger = getLogger()
    try:
        with open(yaml_file, "r") as file_obj:
            f_size = os.stat(file_obj.fileno()).st_size
            if size_constraint_min or size_constraint_max:
                if (
                    f_size < size_constraint_min
                    or f_size > size_constraint_max
                ):
                    log.info(
                        "File size invalid for constraint: %i bytes for %s",
                        f_size,
                        yaml_file,
                    )
                    return None
            yaml_buf = file_obj.read(size_constraint_max)
    except FileNotFoundError:
        return None
    data: Dict[Any, Any] = yaml.safe_load(yaml_buf)
    try:
        reserialized: Dict[Any, Any] = yaml.safe_load(yaml.safe_dump(data))
        if reserialized == data:
            validated_data: Dict[Any, Any] = schema.validate(data)
        else:
            log.info("Data does not pack and unpack as expected")
            return None
    except SchemaError:
        log.info(
            "Data in %s did not validate against schema: %s", yaml_file, schema
        )
        return None
    return validated_data


class attrdict(dict):
    """
    Dictionary which provides attribute access to its keys.

    For best results, use the schemattrdict subclass rather than using this
    directly.
    """

    def __getattr__(self, key):
        """
        get value of key

        >>> a = attrdict({1:2})
        >>> a.__getattr__(1)
        2

        >>> a.__getattr__(2)
        Traceback (most recent call last):
            ...
        AttributeError: 'attrdict' object has no attribute 2
        """
        if key in self:
            return self[key]
        else:
            raise AttributeError(
                "%r object has no attribute %r" % (type(self).__name__, key)
            )

    def __setattr__(self, key, value):
        if key in self:
            raise ValueError(
                "Programmer error: attempt to set an attribute (%s=%r) of an"
                "instance of %r ( which is an attrdict, which provides "
                "read-only access to keys through the attribute interface). "
                "Attributes which are dictionary keys are not allowed to be "
                "set through the attrdict attribute interface. "
                % (key, value, type(self))
            )
        super(attrdict, self).__setattr__(key, value)


class ro_dict(dict):
    """
    This is a dictionary which is not easy to accidentally update.

    It's not a strong read-only protection, as its values may be mutable and
    the dict itself can actually be updated by using the dict type's update
    method instead of using the object's own exception-raising update method
    definedhere.

    We use this instead of the frozendict from PyPI so that we can be an actual
    dict and thus it is trivially compatible with out other dict mixin classes,
    and because we don't need the feature frozendict provides which we don't
    (hashability). Perhaps in the future we'll decide to use frozendict
    instead.

    >>> ro = ro_dict({'a':1,'b':2,'c':3})
    >>> ro['a'] = 2
    Traceback (most recent call last):
         ...
    ValueError: Attempt to set key 'a' in read-only dictionary

    >>> ro = ro_dict({'a':1})
    >>> ro.update({'a':2})
    Traceback (most recent call last):
         ...
    ValueError: Attempt to update read-only dictionary (...)

    """

    def __setitem__(self, key, value):
        """
        raises a ValueError exception when trying to set a key in a ro_dict

        test adding a non-existing key to ro_dict:
        >>> test_ro_dict = ro_dict({"key": "value"})
        >>> test_ro_dict["different_key"] = "other_value"
        Traceback (most recent call last):
        ...
        ValueError: Attempt to set key 'different_key' in read-only dictionary

        test setting an existing key:
        >>> test_ro_dict = ro_dict({"key": "value"})
        >>> test_ro_dict["key"] = "other_value"
        Traceback (most recent call last):
        ...
        ValueError: Attempt to set key 'key' in read-only dictionary
        """
        raise ValueError(
            "Attempt to set key %r in read-only dictionary" % (key,)
        )

    def update(self, *a, **kw):
        """
        raises a ValueError exception when trying to change a ro_dict using the
        update() method

        test updating an existing key:
        >>> test_ro_dict = ro_dict({"key": "value"})
        >>> test_ro_dict.update({"key": "other_value"})
        Traceback (most recent call last):
        ...
        ValueError: Attempt to update read-only dictionary (*({'key': \
'other_value'},), **{})

        test updating a non-existing key:
        >>> test_ro_dict = ro_dict({"key": "value"})
        >>> test_ro_dict.update({"different_key": "other_value"})
        Traceback (most recent call last):
        ...
        ValueError: Attempt to update read-only dictionary \
(*({'different_key': 'other_value'},), **{})
        """
        raise ValueError(
            "Attempt to update read-only dictionary (*%s, **%s)" % (a, kw)
        )


def raw(value):
    """
    Recursively coerces objects into something serializable.

    This tries to return the original unmodified object whenever possible, to
    avoid precluding the possibility of having automatic YAML object references
    when a sub-object occurs multiple times within a parent object.

    >>> raw(3)
    3
    >>> raw("vula")
    'vula'
    >>> raw(True)
    True
    >>> raw(2.8)
    2.8

    >>> intBool = IntBool(1)
    >>> raw(intBool)
    True

    >>> raw(["one", "two", "three"])
    ['one', 'two', 'three']
    >>> raw(("one", "two", "three"))
    ['one', 'two', 'three']
    >>> sorted(raw({"one", "two", "three"}))
    ['one', 'three', 'two']

    >>> raw({"number" : 1, "letter" : "a"})
    {'number': 1, 'letter': 'a'}

    """
    if type(value) in (int, str, bool, float):
        return value
    if isinstance(value, IntBool):
        return bool(value)
    if hasattr(value, '_dict'):
        return value._dict()
    if type(value) in (list, set, tuple):
        new = list(raw(item) for item in value)
        return (
            value
            if type(value) is list and all(a is b for a, b in zip(new, value))
            else new
        )
    if isinstance(value, dict):
        new = {raw(k): raw(v) for k, v in value.items()}
        return (
            value
            if type(value) is dict
            and all(
                k is k_ and v is v_
                for ((k, v), (k_, v_)) in zip(new.items(), value.items())
            )
            else new
        )
    return str(value)


class serializable(dict):
    def _dict(self):
        """Return serializable as a dictionary

        >>> serializable({1:serializable({2:3})})._dict()
        {1: {2: 3}}

        >>> serializable({1:{2:(3,4,5)}})._dict()
        {1: {2: [3, 4, 5]}}
        """
        return {raw(k): raw(v) for k, v in self.items()}


class schemadict(ro_dict, serializable):

    schema = NotImplemented
    default = None

    def __init__(self, *a, **kw):
        self._as_dict = None
        data = copy.deepcopy(self.default) or {}
        kw = {k: v for k, v in kw.items() if v is not None}
        data.update(*a, **kw)
        assert type(data) == dict
        super(schemadict, self).__init__(self.schema.validate(data))

    def __deepcopy__(self, memo):
        return type(self)(copy.deepcopy(dict(self)))

    def copy(self):
        return self.__deepcopy__(None)

    def _dict(self):
        if self._as_dict is None:
            self._as_dict = super(schemadict, self)._dict()
        return self._as_dict


class schemattrdict(attrdict, schemadict):
    pass


class yamlfile(serializable):
    def write_yaml_file(self, path, mode=None, autochown=False):
        if mode:
            Path(path).touch(mode=mode)

        with click.open_file(
            path, mode='w', encoding='utf-8', atomic=True
        ) as fh:
            fh.write(
                yaml.safe_dump(self._dict(), default_style='', sort_keys=False)
            )
        if autochown:
            chown_like_dir_if_root(path)

    @classmethod
    def from_yaml_file(cls, path):
        with click.open_file(path, mode='r', encoding='utf-8') as fh:
            return cls(yaml.safe_load(fh))


class yamlrepr(serializable):
    r"""
    Function to return a YAML representation of a Serializable in human
    readable format
    >>> myObj = serializable(("ab", "cd"))
    >>> myYaml = yamlrepr(myObj)
    >>> myYaml.__repr__()
    'a: b\nc: d\n'
    """

    def __repr__(self):
        """
        Function to return a YAML representation of a Serializable in human
        readable format
        >>> yamlrepr(serializable({2:3}))
        2: 3
        <BLANKLINE>
        """
        return yaml.safe_dump(self._dict(), default_style='', sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str):
        return cls(yaml.safe_load(yaml_str))


class jsonrepr_pp(serializable):
    def __repr__(self):
        r"""
        Function to return a json representation of a Serializable in human
        readable format
        >>> myObj = serializable(("ab", "cd"))
        >>> myJson = jsonrepr_pp(myObj)
        >>> myJson.__repr__()
        '{\n    "a": "b",\n    "c": "d"\n}'
        """
        return json.dumps(self._dict(), indent=4)


class jsonrepr(serializable):
    def __repr__(self):
        """
        Function to return a json representation of a Serializable.
        >>> mySerializable = serializable(("ab", "cd"))
        >>> myJsonRepr = jsonrepr(mySerializable)
        >>> myJsonRepr.__repr__()
        '{"a": "b", "c": "d"}'
        """
        return json.dumps(self._dict())


if pygments is not None:

    #    from pygments.style import Style
    #    from pygments.token import ( Keyword, Name, Comment, String,
    #        Error, Number, Operator, Generic,)
    #
    #    class MyStyle(Style):
    #        default_style = ""
    #        styles = {
    #            Name: 'bold #0f0',
    #        }

    class yamlrepr_hl(yamlrepr):
        def __repr__(self):

            # aaa = list(
            #    pygments.lexers.YamlLexer().get_tokens_unprocessed(
            #        yaml.dump(self._dict(), default_style='', sort_keys=False)
            #    )
            # )

            res = pygments.highlight(
                yaml.safe_dump(
                    self._dict(), default_style='', sort_keys=False
                ),
                pygments.lexers.YamlLexer(),
                pygments.formatters.TerminalTrueColorFormatter(
                    #    style=MyStyle,
                    style='paraiso-dark'
                ),
            )
            return res

    class jsonrepr_hl(jsonrepr):
        def __repr__(self):
            r"""
            Function to return a raw json formatted content with syntax
            highlighting.
            >>> serializableObj = serializable(("ab", "cd"))
            >>> jsonReprObj = jsonrepr(serializableObj)
            >>> jsonReprhlObj = jsonrepr_hl(jsonReprObj)
            >>> jsonReprhlObj.__repr__()
            '\x1b[38;2;231;233;219m{\x1b[39m\n\x1b[38;2;231;233;219m  \x1b[39m\x1b[38;2;91;196;191m"a"\x1b[39m\x1b[38;2;231;233;219m:\x1b[39m\x1b[38;2;231;233;219m \x1b[39m\x1b[38;2;72;182;133m"b"\x1b[39m\x1b[38;2;231;233;219m,\x1b[39m\n\x1b[38;2;231;233;219m  \x1b[39m\x1b[38;2;91;196;191m"c"\x1b[39m\x1b[38;2;231;233;219m:\x1b[39m\x1b[38;2;231;233;219m \x1b[39m\x1b[38;2;72;182;133m"d"\x1b[39m\n\x1b[38;2;231;233;219m}\x1b[39m\n'
            """  # noqa: E501

            res = pygments.highlight(
                json.dumps(self._dict(), indent=2),
                pygments.lexers.JsonLexer(),
                pygments.formatters.TerminalTrueColorFormatter(
                    style='paraiso-dark'
                ),
            )
            return res

else:
    yamlrepr_hl = yamlrepr  # type: ignore
    jsonrepr_hl = jsonrepr  # type: ignore


class Bug(Exception):
    pass


class ConsistencyError(Exception):
    pass


class comma_separated_IPs(object):
    def __init__(self, _str):
        """
        create a list of IP address

        >>> comma_separated_IPs("127.0.0.1,15.15.15.15")
        <comma_separated_IPs('127.0.0.1,15.15.15.15')>
        >>> comma_separated_IPs("fe80::1,fe80::2")
        <comma_separated_IPs('fe80::1,fe80::2')>
        >>> comma_separated_IPs("::1")
        <comma_separated_IPs('::1')>
        >>> comma_separated_IPs("invalid")
        Traceback (most recent call last):
        ...
        ValueError: 'invalid' does not appear to be an IPv4 or IPv6 address
        """
        self._str = str(_str)
        self._items = tuple(
            ip_address(ip) for ip in self._str.split(',') if ip
        )

    def __iter__(self):
        """
        Iterate over ips

        >>> [ip for ip in comma_separated_IPs("::1,192.168.1.1")]
        [IPv6Address('::1'), IPv4Address('192.168.1.1')]
        """
        return iter(self._items)

    def __getitem__(self, idx):
        """
        get item at index

        :param idx: int
        :return: IPv4Address

        >>> test_list = comma_separated_IPs("127.0.0.2,127.0.0.3,127.0.0.4")
        >>> test_list.__getitem__(1)
        IPv4Address('127.0.0.3')


        :param idx: int
        :return: IPv6Address

        >>> test_list = comma_separated_IPs("fe80::1,fe80::2")
        >>> test_list.__getitem__(0)
        IPv6Address('fe80::1')

        """
        return list(self)[idx]

    def __repr__(self):
        """
        Return the type of the class with his IP

        >>> ip = comma_separated_IPs('192.168.0.1')
        >>> ip.__repr__()
        "<comma_separated_IPs('192.168.0.1')>"

        >>> ip = comma_separated_IPs('fe80::1')
        >>> ip.__repr__()
        "<comma_separated_IPs('fe80::1')>"

        """

        """
        get IP

        >>> ips = comma_separated_IPs("192.168.3.2,192.168.0.3,192.168.3.4,
        ... 192.168.0.2,192.168.0.3,192.168.3.4")
        >>> ips.__repr__()
        "<comma_separated_IPs('192.168.3.2,192.168.0.3,192.168.3.4, \
        192.168.0.2,192.168.0.3,192.168.3.4')>"
        """
        return "<%s(%r)>" % (type(self).__name__, self._str)

    def __str__(self):
        """
        Return the comma separated IP addresses as a string

        >>> ip = comma_separated_IPs('fe80::1')
        >>> ip.__str__()
        'fe80::1'

        >>> ip = comma_separated_IPs('192.168.0.1')
        >>> ip.__str__()
        '192.168.0.1'

        >>> ip_multiple = \
        comma_separated_IPs('192.168.29.32,127.0.0.1,149.132.22.70')
        >>> ip_multiple.__str__()
        '192.168.29.32,127.0.0.1,149.132.22.70'

        >>> ip_multiple = \
        comma_separated_IPs('fe80::1,fe80::2,fe80::3')
        >>> ip_multiple.__str__()
        'fe80::1,fe80::2,fe80::3'
        """

        return self._str


class comma_separated_Nets(comma_separated_IPs):
    """
    Instantiate a list of networks

    >>> comma_separated_Nets("blabla")
    Traceback (most recent call last):
       ...
    ValueError: 'blabla' does not appear to be an IPv4 or IPv6 network
    >>> comma_separated_Nets("192.168.0.0/28,192.168.0.1/28")
    Traceback (most recent call last):
       ...
    ValueError: 192.168.0.1/28 has host bits set

    >>> comma_separated_Nets("fe80::1/10,fe80::/10")
    Traceback (most recent call last):
       ...
    ValueError: fe80::1/10 has host bits set

    >>> comma_separated_Nets("192.168.0.0/28,192.168.1.0/25")
    <comma_separated_Nets('192.168.0.0/28,192.168.1.0/25')>

    >>> comma_separated_Nets("fe80::/10,fe80::/10")
    <comma_separated_Nets('fe80::/10,fe80::/10')>
    """

    def __init__(self, _str):
        self._str = str(_str)
        self._items = tuple(
            ip_network(ip) for ip in self._str.split(',') if ip
        )


class constraint(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        """
        Function to return constraint object.
        >>> constraint({4:3})
        constraint({4: 3})
        """
        # FIXME: add kwargs to repr
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join(map(repr, self.args)),
        )

    def validate(self, value):
        """
        >>> constraint.validate(int_range(6,9), 7)
        7
        >>> constraint.validate(int_range(6, 9), 5)
        Traceback (most recent call last):
        ValueError: int_range(6, 9) check failed on False
        """
        # import pdb; pdb.set_trace()
        value = self.constraint(value, *self.args, **self.kwargs)
        if value is not False:
            return value
        else:
            raise ValueError("%s check failed on %r" % (self, value))


class Length(constraint):
    """
    Constraint to check if a string length is equal to, min or max a given
    value.
    """

    @staticmethod
    def constraint(value, length=None, min=None, max=None):
        """
        Validates min and max length of a given string.
        Returns the value of constraints are met else an error is raised.

        >>> Length.constraint("Test", min = 3, max = 5)
        'Test'
        >>> Length.constraint("Vula is cool", length = 12)
        'Vula is cool'
        >>> Length.constraint("Test", length = 3)
        Traceback (most recent call last):
            ...
        ValueError: length is 4, should be 3: 'Test'
        >>> Length.constraint("Test", max = 3)
        Traceback (most recent call last):
            ...
        ValueError: length is 4, should be <=3: 'Test'
        >>> Length.constraint("Test", min = 5)
        Traceback (most recent call last):
            ...
        ValueError: length is 4, should be >=5: 'Test'
        """
        if length is not None and len(value) != length:
            raise ValueError(
                "length is %s, should be %s: %r" % (len(value), length, value)
            )
        if max is not None and len(value) > max:
            raise ValueError(
                "length is %s, should be <=%s: %r" % (len(value), max, value)
            )
        if min is not None and len(value) < min:
            raise ValueError(
                "length is %s, should be >=%s: %r" % (len(value), min, value)
            )
        return value


class int_range(constraint):
    @staticmethod
    def constraint(value, min, max):
        """
        Validates value, which must be an integer between min and max.
        Returns the value if constraints are met, false otherwise.

        >>> int_range.constraint(5, min = 2, max = 10)
        5
        >>> int_range.constraint(5, min = 7, max = 10)
        False
        >>> int_range.constraint(5, min = 2, max = 4)
        False
        >>> int_range.constraint("abc", min = 2, max = 10)
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'abc'
        >>> int_range.constraint(10, 5, 20)
        10
        >>> int_range.constraint(5, 10, 20)
        False
        >>> int_range.constraint(20, 5, 10)
        False
        >>> int_range.constraint(5, 5, 5)
        5
        >>> int_range.constraint(5, 6, 4)
        False
        """
        return min <= int(value) <= max and int(value)


class colon_hex_bytes(bytes):
    def __str__(self):
        """
        Return the hex representation as a string.

        >>> a = colon_hex_bytes.with_len(3).validate(b'ABC')
        >>> a.__str__()
        '41:42:43'
        """
        return ":".join("%x" % byte for byte in self)

    def __repr__(self):
        """
        Return the canonical string representation of the colon_hex_bytes
        object.

        >>> hex_bytes = colon_hex_bytes.with_len(3).validate(b'ABC')
        >>> hex_bytes.__repr__()
        "'41:42:43'"
        """
        return repr(str(self))

    @classmethod
    def with_len(cls, length):
        """
        >>> a = colon_hex_bytes.with_len(3).validate(b'ABC')
        >>> a
        '41:42:43'
        >>> colon_hex_bytes.with_len(3).validate( \
        b'ABCD') # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        schema.SchemaError:
        >>> b = colon_hex_bytes.with_len(3).validate(str(a))
        >>> a == b
        True
        >>> list(a)
        [65, 66, 67]
        >>> a.decode()
        'ABC'
        >>> c = colon_hex_bytes.with_len(4).validate(b'ABCD')
        >>> c
        '41:42:43:44'
        """
        str_len = length * 3 - 1
        return Or(
            And(
                str,
                Length(str_len),
                Use(lambda s: s.split(':')),
                Length(length),
                Use(lambda s: [int(b, 16) for b in s]),
                Use(cls),
            ),
            And(bytes, Length(length), Use(cls)),
            error=f"{{!r}} is not {length} bytes or a {str_len}-char "
            f"colon-separated hex string "
            f"representing {length} bytes",
        )


MACaddr = colon_hex_bytes.with_len(6)
BSSID = colon_hex_bytes.with_len(6)
ESSID = And(str, Length(min=1, max=32))


class b64_bytes(bytes):
    """
    Bytes subclass which automatically stringifies itself to base64, and has a
    repr which shows the first 6 bytes of its base64 encoding.
    """

    def __str__(self):
        """
        Function to return a string representation of entered bytes.

        >>> string = "Test"
        >>> arr = bytearray(string, 'utf-8')
        >>> test = b64_bytes(arr)
        >>> str(test)
        'VGVzdA=='
        >>> b64decode(str(test))
        b'Test'
        """
        return b64encode(self).decode()

    def __repr__(self):
        """
        Function to return a base64 representation of entered bytes

        >>> string = "Vula is cool."
        >>> arr = bytearray(string, 'utf-8')
        >>> b64_bytes(arr).__repr__()
        '<b64:VnVsYS...(13)>'
        """
        return "<b64:%s...(%s)>" % (str(self)[:6], len(self))

    @classmethod
    def with_len(cls, length):
        """
        Produces a schema object which accepts either bytes or base64-encoded
        strings, and returns b64_bytes objects while enforcing a length
        constraint.

        >>> a = b64encode(b'A'*10).decode()
        >>> a, len(a)
        ('QUFBQUFBQUFBQQ==', 16)
        >>> b = b64_bytes.with_len(10).validate(a)
        >>> b
        <b64:QUFBQU...(10)>
        >>> str(b)
        'QUFBQUFBQUFBQQ=='
        >>> bytes(b)
        b'AAAAAAAAAA'
        >>> c = b64_bytes.with_len(10).validate(bytes(b))
        >>> c == b == bytes(b)
        True
        >>> c == b64_bytes.with_len(10).validate(a)
        True

        this test is complicated to be able to pass both with and without the
        bugfix in schema 0.7.4:
        >>> try:
        ...     b64_bytes.with_len(10).validate('123')
        ... except Exception as ex:
        ...     e = ex
        >>> import schema, packaging.version as pkgv
        >>> assert type(e) is schema.SchemaError
        >>> msg = "'123' is not 10 bytes or a 16-char base64 string "\
        "which decodes to 10 bytes"
        >>> if pkgv.parse(schema.__version__) < pkgv.parse('0.7.3'):
        ...     msg += "\\n{!r} is not 10 bytes or a 16-char "
        ...     msg += "base64 string which decodes to 10 bytes"
        >>> assert e.args == (msg,), (e.args, msg)

        """
        b64_length = 4 * ((length // 3) + bool(length % 3))
        return Or(
            And(
                str,
                Length(b64_length),
                Use(b64decode),
                Use(cls),
                Length(length),
            ),
            And(bytes, Length(length), Use(cls)),
            error="{!r} is not %s bytes or a %s-char base64 string which "
            "decodes to %s bytes" % (length, b64_length, length),
            # name = '%s bytes base64-encoded' % (length,), #when we upgrade to
            # the newer schema lib
        )


class IntBool(int):
    """
    This holds values defined as Flexibool in schemas, which allows bools to be
    specified by users in a variety of ways.

    This class exists so that these values can be identified in the 'raw'
    function, which will convert them to normal bools.
    """


Flexibool = And(
    Or(
        bool,
        And(int, lambda n: n in (0, 1)),
        And(
            str,
            Use(
                lambda v: 1
                if v.lower() in ('true', 'yes', 'on', '1', 'y', 'j', 'ja')
                else 0
                if v.lower() in ('false', 'no', 'off', '0', 'n', 'nein', 'nej')
                else 'error'
            ),
        ),
    ),
    Use(IntBool),
    error="invalid value {!r}; must be one of "
    "<true|false|1|0|on|off|yes|no|ja|nein|nej|y|j|n>",
)


class queryable(dict):
    def limit(self, **kw):
        """
        >>> d = {1:{"enabled":True},2:{"enabled":False}}
        >>> d
        {1: {'enabled': True}, 2: {'enabled': False}}
        >>> q = queryable(d)
        >>> q.limit(enabled=True)
        {1: {'enabled': True}}
        >>> q.limit(enabled=False)
        {2: {'enabled': False}}
        >>> q.limit()
        {1: {'enabled': True}, 2: {'enabled': False}}
        """
        return type(self)(
            (name, item)
            for name, item in self.items()
            if all(
                (
                    (v in item[k])
                    if isinstance(item[k], (dict, list, set))
                    else (v == item[k])
                )
                for k, v in kw.items()
            )
        )

    def limit_attr(self, **kw):
        return type(self)(
            (name, item)
            for name, item in self.items()
            if all(
                (
                    (v in getattr(item, k))
                    if isinstance(getattr(item, k), (dict, list, set))
                    else (v == getattr(item, k))
                )
                for k, v in kw.items()
            )
        )

    def by(self, key):
        res = type(self)()
        for item in self.values():
            value = getattr(item, key)

            if isinstance(value, list):
                for subvalue in value:
                    res.setdefault(subvalue, []).append(item)
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subvalue:
                        res.setdefault(subkey, []).append(item)
            else:
                res.setdefault(value, []).append(item)
        return res


class chunkable_values(dict):

    """
    This chunks and unchunks dictionary values.

    So, a long value stored under key k becomes many small keys k00..kNN who's
    values can be concatenated to obtain the original long value.

    This is meant to be used for encoding values too large to fit in a TXT
    record. Therefore the chunk size leaves room for the key size plus a two
    digit chunk number plus one more byte for the equals sign in a ZeroConf TXT
    record.

    This was just written for a quick experiment and should be made more robust
    before actually using it.

    >>> d = chunkable_values(a=1, b='0123456789')
    >>> d.chunk(10)
    {'a': 1, 'b00': '012345', 'b01': '6789'}
    >>> d.chunk(7)
    {'a': 1, 'b00': '012', 'b01': '345', 'b02': '678', 'b03': '9'}
    >>> d.chunk(5).unchunk()
    {'a': 1, 'b': '0123456789'}
    >>> d.chunk(4)
    Traceback (most recent call last):
    AssertionError: no room for data with chunk size 4 and key b
    >>> d.chunk(9).chunk(8).unchunk().unchunk() == d
    True
    """

    def chunk(self, length):
        res = {}
        for k, v in list(self.items()):
            if len(k) + len(str(v)) + 1 <= length:
                res[k] = v
            else:
                c = 0
                cs = length - len(k) - 3
                assert (
                    cs >= 1
                ), "no room for data with chunk size %s and key %s" % (
                    length,
                    k,
                )
                while v:
                    res["%s%02d" % (k, c)] = v[:cs]
                    v = v[cs:]
                    c += 1
        return type(self)(res)

    def unchunk(self):
        """Combines chunks of this dictionary.

        >>> chunkable_values({'a01':'23','a00':'01','a02':'45'}).unchunk()
        {'a': '012345'}
        """
        res = {}
        for k, v in list(sorted(self.items())):
            rk = k[:-2]
            try:
                int(k[-2:])
            except ValueError:
                # Expects a ValueError: invalid literal for int() ...  if the
                # last two digits are not a number it is not a chunked key
                res[k] = v
                continue
            res[rk] = res.get(rk, '') + v
        return type(self)(res)


def addrs_in_subnets(addrs, subnets):
    """
    >>> current_subnets={'10.0.0.0/24': ['10.0.0.9', '10.0.0.51',
    ... '10.0.0.17'], '10.0.1.0/24':
    ... ['10.0.1.22', '10.0.1.73'], '10.0.5.0/24': ['10.0.5.21', '10.0.5.63']}
    >>> addrs = ['10.0.0.0/24','10.0.14.0/24', '10.0.5.0/24']
    >>> addrs_in_subnets(addrs,current_subnets)
    ['10.0.0.0/24', '10.0.5.0/24']

    >>> current_subnets={'fe80::/10':['fe80::1', 'fe80::2'],
    ... 'fe80::1:0/10': ['fe80::1:1', 'fe80::1:6' ],
    ... 'fe80::2:0/10': ['fe80::2:1', 'fe80::2:5' ]}
    >>> addrs = ['fe80::/10', 'fe80::ffff:1/10', 'fe80::2:0/10']
    >>> addrs_in_subnets(addrs, current_subnets)
    ['fe80::/10', 'fe80::2:0/10']

    """
    return [
        addr for addr in addrs if any(addr in subnet for subnet in subnets)
    ]


class KeyFile(yamlrepr_hl, schemattrdict, yamlfile):

    schema = Schema(
        {
            "pq_ctidhP512_sec_key": b64_bytes.with_len(74),
            "pq_ctidhP512_pub_key": b64_bytes.with_len(64),
            "vk_Ed25519_sec_key": b64_bytes.with_len(32),
            "vk_Ed25519_pub_key": b64_bytes.with_len(32),
            "wg_Curve25519_sec_key": b64_bytes.with_len(32),
            "wg_Curve25519_pub_key": b64_bytes.with_len(32),
        }
    )


def organize_dbus_if_active():

    """
    Returns a dbus proxy to organize, if it is running. Exits otherwise.

    This is for commands that shouldn't dbus-activate it.
    """

    bus = pydbus.SystemBus()
    if bus.dbus.NameHasOwner(_ORGANIZE_DBUS_NAME):
        return bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
    elif _ORGANIZE_DBUS_NAME in bus.dbus.ListActivatableNames():
        raise Exit(
            "Organize is not running (but it is dbus-activatable; use 'vula"
            "start' to start it.)."
        )
    else:
        raise Exit("Organize dbus service is not configured")


def sfmt(
    a,
    base=1000,
    places=0,
    unit='',
    infix='',
    preprefix='',
    prefixes="kMGTPEZYH",
):
    """
    >>> sfmt(0), sfmt(1), sfmt(999)
    ('0', '1', '999')
    >>> sfmt(1e3)
    '1k'
    >>> sfmt(1000)
    '1k'
    >>> sfmt(1499)
    '1k'
    >>> sfmt(1499, places=5)
    '1.49900k'
    >>> sfmt(1500)
    '2k'
    >>> sfmt(1e4)
    '10k'
    >>> sfmt(1_000_000)
    '1M'
    >>> sfmt(10_000_000)
    '10M'
    >>> sfmt(10**27)
    '1H'
    >>> sfmt(10**30)
    '1000H'
    >>> sfmt(1023,base=1024,unit="B",infix="i",prefixes="KMG",preprefix=" ")
    '1023 B'
    >>> sfmt(1024,base=1024,unit="B",infix="i",prefixes="KMG",preprefix=" ")
    '1 KiB'
    >>> sfmt(100_000,base=1024,unit="B",infix="i",prefixes="KMG",preprefix=" ")
    '98 KiB'
    >>> sfmt(1_000_000,base=1024,unit="B",infix="i",prefixes="KMG",
    ... preprefix=" ")
    '977 KiB'
    >>> sfmt(10_000_000, base=1024, unit="B", infix="i", prefixes="KMG",
    ... preprefix=" ", places=1)
    '9.5 MiB'

    """
    i = 0
    while base <= a and i < len(prefixes):
        a /= base
        i += 1
    return (
        ("{:.%sf}{}" % (places if i else 0,))
        .format(
            a,
            preprefix + (prefixes[i - 1].strip() + infix if i else '') + unit,
        )
        .strip()
    )


pprint_bytes = lambda b: sfmt(
    b,
    base=1024,
    unit="B",
    preprefix=" ",
    infix="i",
    prefixes="KMGTPEZYH",
    places=2,
)
format_byte_stats = lambda stats: {
    k: pprint_bytes(v) for k, v in stats.items()
}


def escape_ansi(line: str) -> str:
    """
    Removes ANSI escape sequences from the string.

    >>> escape_ansi("\033[0;31mclean\033[0m")
    'clean'
    >>> escape_ansi("clean")
    'clean'
    """
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub('', line)


if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
