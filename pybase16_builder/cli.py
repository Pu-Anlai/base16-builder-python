import argparse
from . import updater, builder, injector
from .shared import rel_to_cwd


def build_mode(arg_namespace):
    """Check command line arguments and run build function."""
    custom_temps = arg_namespace.template or []
    temp_paths = [rel_to_cwd('templates', temp) for temp in custom_temps]

    try:
        builder.build(templates=temp_paths,
                      schemes=arg_namespace.scheme,
                      base_output_dir=arg_namespace.output)
    except (LookupError, PermissionError) as exception:
        if isinstance(exception, LookupError):
            print('Necessary resources for building not found in current '
                  'working directory.')
        if isinstance(exception, PermissionError):
            print("No write permission for output directory.")


def inject_mode(arg_namespace):
    """Check command line arguments and run build function."""

    try:
        injector.inject_into_files(arg_namespace.scheme, arg_namespace.file)
    except (IndexError, FileNotFoundError, LookupError,
            PermissionError, IsADirectoryError, ValueError) as exception:
        if isinstance(exception, ValueError):
            print('Pattern {} matches more than one scheme.'.format(
                *arg_namespace.scheme))
        elif isinstance(exception, IndexError):
            print('"{}" has no valid injection marker lines.'.format(
                exception.args[0]))
        elif isinstance(exception, FileNotFoundError):
            print('Lacking resource "{}" to complete operation.'.format(
                exception.filename))
        elif isinstance(exception, PermissionError):
            print('No write permission for current working directory.')
        elif isinstance(exception, IsADirectoryError):
            print('"{}" is a directory. Provide a *.yaml scheme file instead.'
                  .format(exception.filename))
        elif isinstance(exception, LookupError):
            print('No scheme "{}" found.'
                  .format(*arg_namespace.scheme))


def update_mode(arg_namespace):
    """Check command line arguments and run update function."""
    try:
        updater.update(custom_sources=arg_namespace.custom)
    except (PermissionError, FileNotFoundError) as exception:
        if isinstance(exception, PermissionError):
            print('No write permission for current working directory.')
        if isinstance(exception, FileNotFoundError):
            print('Necessary resources for updating not found in current '
                  'working directory.')


def run():
    arg_namespace = argparser.parse_args()
    arg_namespace.func(arg_namespace)


argparser = argparse.ArgumentParser(prog='pybase16')
subparsers = argparser.add_subparsers(dest='mode')
subparsers.required = True  # workaround for versions <3.7

update_parser = subparsers.add_parser(
    'update',
    help='update: download all base16 scheme and template repositories')
update_parser.set_defaults(func=update_mode)
update_parser.add_argument(
    '-c', '--custom', action='store_const', const=True,
    help="update repositories but don't update source files")

build_parser = subparsers.add_parser(
    'build',
    help='build: build base16 colorschemes from templates')
build_parser.set_defaults(func=build_mode)
build_parser.add_argument(
    '-o', '--output',
    help="specifiy a target directory for the build output")
build_parser.add_argument(
    '-t', '--template', action='append', metavar='TEMP',
    help="restrict operation to specific templates (must correspond to a directory in ./templates); can be specified more than once")
build_parser.add_argument(
    '-s', '--scheme', action='append',
    help='restrict operation to specific schemes; (properly escaped) wildcards allowed')

inject_parser = subparsers.add_parser(
    'inject',
    help='inject: inject a colorscheme into one or multiple files')
inject_parser.set_defaults(func=inject_mode)
inject_parser.add_argument(
    '-f', '--file', action='append', required=True,
    help='provide paths to files into which you wish to inject a colorscheme; can be specified more than once')
inject_parser.add_argument(
    '-s', '--scheme', action='append', required=True,
    help='select a scheme; allows for wildcards')
