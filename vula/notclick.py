import inspect
import os
import shutil
import sys
from functools import reduce, wraps

import click
import packaging.version as pkgv
from click.exceptions import Exit  # noqa: F401
from schema import Optional, Schema

"""
This file contains various click-related bits of vula. None of this is
strictly necessary; it is mostly used for debugging. It would be fine to remove
the cls=Debuggable from __main__.py and remove all of the DualUse
decorators from organize etc (using plain-old click.command to decorate the
organize class should work) and the software would still run the way we intend
it to be run in production.

So what do these magical click things do? They make it so that you can use -d
to do a post-mortem when there are exceptions (except maybe not in glib
threads... sad). They also make it so that you can run class methods as
subcommands, and so that there are subcommands for accessing attributes.

Eg, this:
    vula organize sync
will instantiate an organize object, loads its state, and then call the
object's sync() method. (Note that the way we actually intend sync to be called
is "vula sync" which calls Organize's sync method via dbus; this "vula
organize sync" method is instantiating an organize object from its state file
and calling the method on that.)

Or, this: vula -d peer.Descriptor --addrs 10.168.128.160 --c
vdDpRSGtsqvui8dox0iBq0SSp/zXSEU2dx5s5x+qcquSp0oIWgDuqJw50e9wrIuGub+SXzU0s5EIR
H49QmNYDw== --dt
86400 --e false --hostname wg-mdns-test3.local.  --pk
EqcQ5gYxzGtzg7B4xi83kLyfuSMp8Kv3cmAJMs12nDM= --port 5354 --r '' --s
T6htsKgwCp5MAXjPiWxtVkccg+K2CePsVa7uyUgxE2ouYKXg2qNL+0ut3sSbVTYjzFGZSCO6n80SR
aR+BIeOCg== --vf
1606276812 --vk 90Y5JGEjoklSDw51ffoHYXhWs49TTnCQ/D5yBbuf3Zg= valid

...will instantiate a Descriptor object and verify that its signature is
correct.

Note that the first example does not require -d, but the second one does:
automatic resolution of dotted attribute paths only happens in the top-level
command and only when debug mode is enabled. The first example, meanwhile, uses
the fact that the Organize class is a DualUse.

Another example which relies on Debuggable, and works with a function that
isn't decorated at all (types are inferred from type annotations):
    sudo vula -d configure._reconfigure_restart_systemd_services  --help

One more example, of chaining the attribute-getting functions:
    sudo vula organize state system_state current_subnets

Anyway, if this gets in the way we can get rid of some or all of it.
"""


class OrderedGroup(click.Group):
    def list_commands(self, ctx):
        return list(self.commands)


class Debuggable(OrderedGroup):

    """
    This is a subclass of click.Group which adds a --debug option which enables
    two features which are useful for debugging:

        - It will drop to a pdb.post_mortem shell after any unhandled exception

        - It allows for automatic commandline access to any function annotated
          with basic types (str, int, maybe others?)

    To use it, just decorate with @Debuggable.command() where you would
    otherwise be using @click.group()
    """

    def __init__(self, scope=None, **attrs):
        self.scope = scope or {}
        super(Debuggable, self).__init__(**attrs)
        self.params.append(
            click.Option(
                ('-d', '--debug/--no-debug'),
                show_default=True,
                hidden=not os.environ.get('DEBUG'),
                is_flag=True,
                default=(
                    os.environ.get('DEBUG')
                    and sys.stdin.isatty()
                    and sys.stdout.isatty()
                ),
                help="Drop to a pdb.post_mortem shell upon uncaught exception "
                "(default True if DEBUG env var is set and stdin/out are "
                "ttys, False otherwise)",
            )
        )

    def invoke(self, ctx):
        try:
            return super(Debuggable, self).invoke(ctx)
        except Exception as ex:
            if isinstance(ex, click.exceptions.ClickException):
                raise ex
            if isinstance(ex, click.exceptions.Exit):
                raise ex
            if ctx.params.get('debug'):
                import pdb
                import traceback

                tb = sys.exc_info()[2]
                traceback.print_tb(tb)
                print(
                    "stopping to allow inspecting exception:\n\n    "
                    "%r\n\ntype c to continue to "
                    "post-mortem frame, or q to quit.\n " % (ex,)
                )
                pdb.set_trace()
                print("pdb.post_mortem on %r:" % (ex,))
                pdb.post_mortem(tb)
            else:
                raise ex

    def get_command(self, ctx, command):

        if command in self.commands:
            return super(Debuggable, self).get_command(ctx, command)

        elif ctx.params.get('debug'):
            try:
                cmd = reduce(
                    lambda a, b: a.get(b)
                    if type(a) is dict
                    else getattr(a, b),
                    command.split('.'),
                    self.scope,
                )
            except Exception as ex:
                print(ex)
                return None
            if isinstance(cmd, click.core.Command):
                return cmd
            elif hasattr(cmd, 'cli') and isinstance(
                cmd.cli, click.core.Command
            ):
                return cmd.cli
            elif callable(cmd):
                return _click_command_from_annotated_function(cmd)


def _click_command_from_annotated_function(cmd):

    """
    This metaprogramming nonsense is only used for development, and hardly even
    that.

    There is actually a library called "autoclick" which presumably does a
    better job of doing what this function is doing.
    """

    @click.command()
    def wrapped(**kw):
        print(cmd(**kw))

    spec = inspect.getfullargspec(cmd)
    none = object()
    defaults = list(spec.defaults or ())
    defaults = [none] * (len(spec.args) - len(defaults)) + defaults
    assert len(defaults) == len(spec.args), "logic error"
    for name, default in zip(spec.args, defaults):
        if default is none:
            wrapped = click.argument(name, type=spec.annotations[name])(
                wrapped
            )
        else:
            wrapped = click.option(
                '--' + name,
                show_default=True,
                default=default,
                type=spec.annotations[name],
            )(wrapped)
    return wrapped


class DualUse(click.Group):

    """
    @DualUse.object() is a class decorator which enables class instances to be
    usable both as normal python objects and as click commandline functions.

    Methods which should be cli accessible should be decorated with
    @DualUse.method() or @property.
    """

    def __init__(self, *a, **kw):
        callback = kw.pop('callback')

        @wraps(callback)
        @click.pass_context
        def wrapper(ctx, *a, **kw):
            instance = callback(*a, **kw)
            if 'magic_instance' not in ctx.meta.setdefault(
                self.callback.__name__, {}
            ):
                ctx.meta[self.callback.__name__]['magic_instance'] = instance
            return instance

        super(DualUse, self).__init__(callback=wrapper, *a, **kw)

    @property
    def all_commands(self):
        """
        Return dictionary of DualUse methods and child classes, with
        self.commands applied on top of it.

        (FIXME: possibly wg.Interface is the only DualUse.object that actually
        uses self.commands/add_command? if so, this could be renamed
        'commands' if the link commands were ported to a nested dualuse
        object...)
        """
        res = {
            value.cli.name: value.cli
            for value in vars(self).values()
            if hasattr(value, 'cli') and value.cli is not self
        }
        res.update(**self.commands)
        return res

    def list_commands(self, ctx):
        return list(self.all_commands.keys()) + [
            name
            for name, value in vars(self.callback).items()
            if isinstance(value, property) and name != "__wrapped__"
        ]

    def get_command(self, ctx, name):
        """
        This got way out of hand. The 'else' branch in this method is just used
        for debugging, and not for everyday use. It allows accessing attributes
        recursively, so you can say things like "vula organize state
        system_state our_wg_pk" and it will print the pk. But, for certain
        objects, it hits max recursion depth, and I haven't figured out why
        yet. I reserve the right to remove this unsupported magic in the
        future.
        """
        res = self.all_commands.get(name)

        if res:
            return res

        else:

            @click.group(
                name=name,
                cls=type(self),
                invoke_without_command=True,
                help="Read %r property of %s object"
                % (name, self.callback.__name__),
            )
            @click.pass_context
            class _property_printer(object):
                @property
                def value(self_):
                    try:
                        return getattr(
                            ctx.meta[self.callback.__name__]['magic_instance'],
                            name,
                        )
                    except Exception as ex:
                        click.echo(ex)

                def __init__(self_, ctx):
                    if ctx.invoked_subcommand is None:
                        echo_maybepager(str(self_.value))

                def __getattr__(self_, name):
                    return getattr(self_.value, name)

            _property_printer.callback.__name__ += ':' + name

            return _property_printer

    @classmethod
    def method(cls, opts=(), *a, **kw):
        """
        Decorator to make methods of DualUse.object classes cli-accessible
        """

        def decorator(f):
            @wraps(f)
            def wrapper(*a, **kw):
                ctx = click.get_current_context()
                instance = ctx.meta[f.__qualname__.split('.')[0]][
                    'magic_instance'
                ]
                res = f(instance, *a, **kw)
                if res:
                    res = str(res)
                    if res[-1] == '\n':
                        res = res[:-1]
                    click.echo(res)

            wrapper.__doc__ = f.__doc__
            decos = opts + (click.command(*a, **kw),)
            wrapper = reduce(lambda a, b: b(a), decos, wrapper)
            f.cli = wrapper
            # note: returning undecorated function, which has click command
            # attached to it
            return f

        return decorator

    @classmethod
    def object(cls, *a, **kw):
        """
        Decorator which installs an object instantiation cli in the 'cli'
        attribute of a class.
        """

        def decorator(f):
            f.cli = wraps(f)(
                click.group(cls=cls, **kw)(schema2click_options(f))
            )
            return f

        return decorator


def _make_type(schema):
    class _type(click.ParamType):
        """
        Note that these click types have awful looking type names currently, as
        the name is literally the whole definition. This will hopefully look
        better when we upgrade to the new version of the schema module which
        allows schemas to have proper names, so we won't need to see the whole
        schema DSL source in our --help output.
        """

        name = str(schema)

        def convert(self, value, param, ctx):
            return Schema(schema).validate(value)

    return _type


def schema2click_options(f):
    if hasattr(f, 'schema'):
        for key, sub_schema in f.schema._schema.items():
            if type(key) is Optional:
                key = key._schema
            default = (getattr(f, 'default') or {}).get(key)
            _type = _make_type(sub_schema)
            f = click.option(
                "--%s" % (key,),
                type=_type(),
                default=default,
                show_default=True,
            )(f)
    return f


def red(s):
    """
    Formats the given string 's' to red foreground color.

    >>> red_string = "This text is red"
    >>> print(red(red_string))
    \x1b[31mThis text is red\x1b[0m
    """
    return click.style(s, fg="red")


def green(s):
    """
    Formats the given string 's' to green foreground color.

    >>> green_string = "This text is green"
    >>> print(green(green_string))
    \x1b[32mThis text is green\x1b[0m
    """
    return click.style(s, fg="green")


def blue(s):
    """
    Formats the given string 's' to blue foreground color.

    >>> blue_string = "This text is blue"
    >>> print(blue(blue_string))
    \x1b[34mThis text is blue\x1b[0m
    """
    return click.style(s, fg="blue")


def yellow(s):
    """
    Formats the given string 's' to yellow foreground color.

    >>> yellow_string = "This text is yellow"
    >>> print(yellow(yellow_string))
    \x1b[33mThis text is yellow\x1b[0m
    """
    return click.style(s, fg="yellow")


def bold(s):
    """
    Formats the given string 's' to be bold.

    >>> bold_string = "This text is bold"
    >>> print(bold(bold_string))
    \x1b[1mThis text is bold\x1b[0m
    """
    return click.style(s, bold=True)


def echo_maybepager(s):
    if s.count("\n") < shutil.get_terminal_size()[1]:
        click.echo(s)
    else:
        click.echo_via_pager(s)


def shell_complete_helper(fn):
    """
    This is a helper to maintain compatibility with both click 7.x and 8.x.

    We could pass the old "autocompletion" argument to click 7.x but instead we
    pass nothing because autocompletion didn't work there anyway.
    """
    if pkgv.parse(click.__version__) >= pkgv.parse('8.0.0'):
        return dict(shell_complete=fn)
    return {}
