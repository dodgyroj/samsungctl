# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import collections
import json
import logging
import os
import socket
import errno


try:
    from . import __doc__ as doc
    from . import __title__ as title
    from . import __version__ as version
    from . import exceptions
    from . import Remote
    from . import key_mappings
    from .config import Config

except ValueError:
    import sys
    path = os.path.dirname(__file__)
    if not path:
        path = os.path.dirname(sys.argv[0])
    if not path:
        path = os.getcwd()

    sys.path.insert(0, os.path.abspath(os.path.join(path, '..')))

    from samsungctl import __doc__ as doc
    from samsungctl import __title__ as title
    from samsungctl import __version__ as version
    from samsungctl import exceptions
    from samsungctl import Remote
    from samsungctl import key_mappings
    from samsungctl.config import Config


def _read_config():
    config = collections.defaultdict(lambda: None, {
        "name": "samsungctl",
        "description": "PC",
        "id": "",
        "method": "legacy",
        "timeout": 0,
    })

    file_loaded = False
    directories = []

    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        directories.append(xdg_config)

    directories.append(os.path.join(os.getenv("HOME"), ".config"))
    directories.append("/etc")

    for directory in directories:
        path = os.path.join(directory, "samsungctl.conf")
        try:
            config_file = open(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                continue
            else:
                raise
        else:
            file_loaded = True
            break

    if not file_loaded:
        return config

    with config_file:
        try:
            config_json = json.load(config_file)
        except ValueError as e:
            message = "Warning: Could not parse the configuration file.\n  %s"
            logging.warning(message, e)
            return config

        config.update(config_json)

    return config


def keys_help(keys):
    import sys

    key_groups = {}
    max_len = 0

    if not keys or keys == [None]:
        keys = key_mappings.KEYS.values()

    for key in keys:
        if key is None:
            continue

        group = key.group
        key = str(key)
        if group not in key_groups:
            key_groups[group] = []

        if key not in key_groups[group]:
            key_groups[group] += [key]
            max_len = max(max_len, len(key) - 4)

    print('Available keys')
    print('=' * (max_len + 4))
    print()
    print('Note: Key support depends on TV model.')
    print()

    for group in sorted(list(key_groups.keys())):
        print('    ' + group)
        print('    ' + ('-' * max_len))
        print('\n'.join(key_groups[group]))
        print()
    sys.exit(0)


def get_key(key):
    if key in key_mappings.KEYS:
        return key_mappings.KEYS[key]
    else:
        logging.warning("Warning: Key {0} not found.".format(key))


def main():
    epilog = "E.g. %(prog)s --host 192.168.0.10 --name myremote KEY_VOLDOWN"
    parser = argparse.ArgumentParser(
        prog=title,
        description=doc,
        epilog=epilog
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {0}".format(version)
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="increase output verbosity"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress non-fatal output"
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="interactive control"
    )
    parser.add_argument(
        "--host",
        help="TV hostname or IP address"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="TV port number (TCP)"
    )
    parser.add_argument(
        "--method",
        help="Connection method (legacy or websocket)"
    )
    parser.add_argument(
        "--name",
        help="remote control name"
    )
    parser.add_argument(
        "--description",
        metavar="DESC",
        help="remote control description"
    )
    parser.add_argument(
        "--id",
        help="remote control id"
    )
    parser.add_argument(
        "--volume",
        type=int,
        help=(
            "sets the TV volume to the entered value, a value of -1 will "
            "display the volume level"
        )
    )
    parser.add_argument(
        "--brightness",
        type=int,
        help=(
            "sets the TV brightness level to the entered value, "
            "a value of -1 will display the brightness level"
        )
    )
    parser.add_argument(
        "--contrast",
        type=int,
        help=(
            "sets the TV contrast level to the entered value, "
            "a value of -1 will display the contrast level"
        )
    )
    parser.add_argument(
        "--sharpness",
        type=int,
        help=(
            "sets the TV sharpness level to the entered value, "
            "a value of -1 will display the sharpness level"
        )
    )
    parser.add_argument(
        "--mute",
        type=str,
        choices=['off', 'on', 'state'],
        help=(
            "sets the mute on or off (not a toggle), "
            "state displays if the mute if on or off"
        )
    )

    parser.add_argument(
        "--source",
        type=str,
        help=(
            "changes the input source to the one specified. "
            "You can either enter the TV source name "
            "eg: HDMI1 HDMI2, USB, PC...."
            "or you can enter the programmed label for the source. "
            "This is going to be what is displayed on the OSD when you change "
            "the source from the remote. If you enter 'state' for the source "
            "name it will print out the currently "
            "active source label and name."
        )
    )

    parser.add_argument(
        "--source-label",
        type=str,
        help=(
            "changes the label for a source. "
            "If you do not use --source to specify the source to change the "
            "label on. It will automatically default to the currently "
            "active source. If you set the label to 'state' it will print out "
            "the current label for a source if specified using --source or "
            "the currently active source"
        )
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="socket timeout in seconds (0 = no timeout)"
    )

    parser.add_argument(
        "--start-app",
        help="start an application --start-app \"Netflix\""
    )
    parser.add_argument(
        "--app-metadata",
        help=(
            "pass options string of information the application "
            "can use when it starts up. And example would be the browser. "
            "To have it open directly to a specific URL you would enter: "
            "\"http\/\/www.some-web-address.com\". wrapping the meta data in "
            "quotes will reduce the possibility of a command line parser "
            "error."
        )
    )
    parser.add_argument(
        "--key-help",
        action="store_true",
        help="print available keys. (key support depends on tv model)"
    )
    parser.add_argument(
        "key",
        nargs="*",
        default=[],
        type=get_key,
        help="keys to be sent (e.g. KEY_VOLDOWN)"
    )

    args = parser.parse_args()

    if args.quiet:
        log_level = logging.ERROR
    elif not args.verbose:
        log_level = logging.WARNING
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    if args.key_help:
        keys_help(args.key)

    config = _read_config()
    config.update({k: v for k, v in vars(args).items() if v is not None})

    if not config["host"]:
        logging.error("Error: --host must be set")
        return

    config = Config(**config)
    config.log_level = log_level

    try:
        with Remote(config) as remote:
            if args.interactive:
                logging.getLogger().setLevel(logging.ERROR)
                from . import interactive
                interactive.run(remote)
            elif config.method == 'websocket' and args.start_app:
                app = remote.get_application(args.start_app)
                if args.app_metadata:
                    app.run(args.app_metadata)
                else:
                    app.run()

            else:
                for key in args.key:
                    if key is None:
                        continue
                    key(remote)

            if args.volume is not None:
                if args.volume == -1:
                    print('Volume:', remote.volume, '%')
                else:
                    remote.volume = args.volume

            elif args.mute is not None:
                if args.mute == 'state':
                    print('Mute:', 'ON' if remote.mute else 'OFF')
                else:
                    remote.mute = args.mute == 'on'

            if args.brightness is not None:
                if args.brightness == -1:
                    print('Brightness:', remote.brightness, '%')
                else:
                    remote.brightness = args.brightness

            if args.contrast is not None:
                if args.contrast == -1:
                    print('Contrast:', remote.contrast, '%')
                else:
                    remote.contrast = args.contrast

            if args.sharpness is not None:
                if args.sharpness == -1:
                    print('Sharpness:', remote.sharpness, '%')
                else:
                    remote.sharpness = args.sharpness

            if args.source_label is not None:
                if args.source is None:
                    if args.source_label == 'state':
                        print('Source Label:', remote.source.label)
                    else:
                        remote.source.label = args.remote_label
                else:
                    for source in remote.sources:
                        if args.source in (source.label, source.name):
                            if args.source_label == 'state':
                                print('Source Label:', source.label)
                            else:
                                source.label = args.source_label
                            break

            elif args.source is not None:
                if args.source == 'state':
                    source = remote.source
                    print(
                        'Source: Label =', source.label,
                        'Name =', source.name
                    )
                else:
                    remote.source = args.source

    except exceptions.ConnectionClosed:
        logging.error("Error: Connection closed!")
    except exceptions.AccessDenied:
        logging.error("Error: Access denied!")
    except exceptions.ConfigUnknownMethod:
        logging.error("Error: Unknown method '{}'".format(config.method))
    except socket.timeout:
        logging.error("Error: Timed out!")
    except OSError as e:
        logging.error("Error: %s", e.strerror)


if __name__ == "__main__":
    main()
