"""
*vula* common functions.
"""
from __future__ import annotations
import os
import sys
import inspect
import codecs
import pdb
from logging import Logger, getLogger
from typing import Any, Dict, Optional
from functools import reduce
from schema import (
    Schema,
    And,
    Use,
    Optional as Optional_,
    Or,
    Regex,
    SchemaError,
)
from base64 import b64decode, b64encode
import yaml
import json
import copy
from ipaddress import (
    IPv4Network,
    IPv4Address,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)
from pathlib import Path
import pydbus
import click
from .click import DualUse, red, green, yellow, bold, Exit
from .constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH

try:
    import pygments
    from pygments import highlight, lexers, formatters
except ImportError:
    pygments = None

bp = pdb.set_trace

memoize = lambda f: (
    lambda d={}: lambda *a: d.setdefault(a, a in d or f(*a))
)()


def chown_like_dir(path):
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
        if key in self:
            return self[key]
        else:
            raise AttributeError(
                "%r object has no attribute %r" % (type(self).__name__, key)
            )

    def __setattr__(self, key, value):
        if key in self:
            raise ValueError(
                "Programmer error: attempt to set an attribute (%s=%r) of an instance of %r (which is an attrdict, which provides read-only access to keys through the attribute interface). Attributes which are dictionary keys are not allowed to be set through the attrdict attribute interface."
                % (key, value, type(self),)
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
    """

    def __setitem__(self, key, value):
        raise ValueError(
            "Attempt to set key %r in read-only dictionary" % (key,)
        )

    def update(self, *a, **kw):
        raise ValueError(
            "Attempt to update read-only dictionary (*%s, **%s)" % (a, kw,)
        )


def raw(value):
    """
    Recursively coerces objects into something serializable.

    This tries to return the original unmodified object whenever possible, to
    avoid precluding the possibility of having automatic YAML object references
    when a sub-object occurs multiple times within a parent object.
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
            chown_like_dir(path)

    @classmethod
    def from_yaml_file(cls, path):
        with click.open_file(path, mode='r', encoding='utf-8') as fh:
            return cls(yaml.safe_load(fh))


class yamlrepr(serializable):
    def __repr__(self):
        return yaml.safe_dump(self._dict(), default_style='', sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str):
        return cls(yaml.safe_load(yaml_str))


class jsonrepr_pp(serializable):
    def __repr__(self):
        return json.dumps(self._dict(), indent=4)


class jsonrepr(serializable):
    def __repr__(self):
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
                    style='paraiso-dark',
                ),
            )
            return res

    class jsonrepr_hl(jsonrepr):
        def __repr__(self):

            res = pygments.highlight(
                json.dumps(self._dict(), indent=2),
                pygments.lexers.JsonLexer(),
                pygments.formatters.TerminalTrueColorFormatter(
                    style='paraiso-dark',
                ),
            )
            return res


else:
    yamlrepr_hl = yamlrepr
    jsonrepr_hl = jsonrepr


class Bug(Exception):
    pass


class comma_separated_IPs(object):
    def __init__(self, _str):
        self._str = str(_str)
        self._items = tuple(
            ip_address(ip) for ip in self._str.split(',') if ip
        )

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, idx):
        return list(self)[idx]

    def __repr__(self):
        return "<%s(%r)>" % (type(self).__name__, self._str)

    def __str__(self):
        return self._str


class comma_separated_Nets(comma_separated_IPs):
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
        # FIXME: add kwargs to repr
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join(map(repr, self.args)),
        )

    def validate(self, value):
        value = self.constraint(value, *self.args, **self.kwargs)
        if value is not False:
            return value
        else:
            raise ValueError("%s check failed on %r" % (self, value))


class Length(constraint):
    @staticmethod
    def constraint(value, length=None, min=None, max=None):
        if length is not None and len(value) != length:
            raise ValueError(
                "length is %s, should be %s: %r" % (len(value), length, value)
            )
        if max is not None and len(value) > max:
            raise ValueError(
                "length is %s, should be >=%s: %r" % (len(value), max, value)
            )
        if min is not None and len(value) < min:
            raise ValueError(
                "length is %s, should be <=%s: %r" % (len(value), max, value)
            )
        return value


class int_range(constraint):
    @staticmethod
    def constraint(value, min, max):
        return min <= int(value) <= max and int(value)


class colon_hex_bytes(bytes):
    def __str__(self):
        return ":".join("%x" % byte for byte in self)

    def __repr__(self):
        return repr(str(self))

    @classmethod
    def with_len(cls, length):
        """
        >>> a = colon_hex_bytes.with_len(3).validate(b'ABC')
        >>> a
        '41:42:43'
        >>> colon_hex_bytes.with_len(3).validate(b'ABCD') # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        schema.SchemaError:
        >>> b = colon_hex_bytes.with_len(3).validate(str(a))
        >>> a == b
        True
        >>> list(a)
        [65, 66, 67]
        >>> a.decode()
        'ABC'
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
            error="{!r} is not %s bytes or a %s-char colon-separated hex string representing %s bytes"
            % (length, str_len, length),
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
        return b64encode(self).decode()

    def __repr__(self):
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
        >>> msg = "'123' is not 10 bytes or a 16-char base64 string which decodes to 10 bytes"
        >>> if pkgv.parse(schema.__version__) < pkgv.parse('0.7.4'):
        ...     msg += "\\n{!r} is not 10 bytes or a 16-char base64 string which decodes to 10 bytes"
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
            And(bytes, Length(length), Use(cls),),
            error="{!r} is not %s bytes or a %s-char base64 string which decodes to %s bytes"
            % (length, b64_length, length),
            # name = '%s bytes base64-encoded' % (length,), # when we upgrade to the newer schema lib
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
                else 'error',
            ),
        ),
    ),
    Use(IntBool),
    error="invalid value {!r}; must be one of <true|false|1|0|on|off|yes|no|ja|nein|nej|y|j|n>",
)


class queryable(dict):
    def limit(self, **kw):
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
                assert cs >= 1, (
                    "no room for data with chunk size %s and key %s"
                    % (length, k)
                )
                while v:
                    res["%s%02d" % (k, c)] = v[:cs]
                    v = v[cs:]
                    c += 1
        return type(self)(res)

    def unchunk(self):
        res = {}
        for k, v in list(sorted(self.items())):
            try:
                rk, c = k[:-2], int(k[-2:])
            except Exception as ex:
                res[k] = v
                continue
            res[rk] = res.get(rk, '') + v
        return type(self)(res)


def addrs_in_subnets(addrs, subnets):
    return [
        addr for addr in addrs if any(addr in subnet for subnet in subnets)
    ]


class KeyFile(yamlrepr_hl, schemattrdict, yamlfile):

    schema = Schema(
        {
            "pq_csidhP512_sec_key": Or(
                b64_bytes.with_len(37), b64_bytes.with_len(74)
            ),
            "pq_csidhP512_pub_key": b64_bytes.with_len(64),
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
            "Organize is not running (but it is dbus-activatable; use 'vula start' to start it.)."
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
    >>> sfmt(1023, base=1024, unit="B", infix="i", prefixes="KMG", preprefix=" ")
    '1023 B'
    >>> sfmt(1024, base=1024, unit="B", infix="i", prefixes="KMG", preprefix=" ")
    '1 KiB'
    >>> sfmt(100_000, base=1024, unit="B", infix="i", prefixes="KMG", preprefix=" ")
    '98 KiB'
    >>> sfmt(1_000_000, base=1024, unit="B", infix="i", prefixes="KMG", preprefix=" ")
    '977 KiB'
    >>> sfmt(10_000_000, base=1024, unit="B", infix="i", prefixes="KMG", preprefix=" ", places=1)
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


if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
