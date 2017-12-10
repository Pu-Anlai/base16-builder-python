import sys
import argparse
from copy import copy
from . import updater, builder, injector
from .shared import rel_to_cwd


BUILD_MODE_ID = 0
INJECT_MODE_ID = 1
UPDATE_MODE_ID = 2


def count_arguments(*args):
    """Takes in argument attributes from an argparse Namespace object and
    counts how many of them are not None."""
    arg_count = len([x for x in args if x is not None])
    return arg_count


def handle_exit_exception(mode, exception):
    """Print an appropriate error message for $mode and $exception and exit the
    program."""
    if mode == BUILD_MODE_ID:
        if isinstance(exception, LookupError):
            print('Necessary resources for building not found in current '
                  'working directory.')
        if isinstance(exception, PermissionError):
            print("No write permission for output directory.")

    elif mode == INJECT_MODE_ID:
        if isinstance(exception, IndexError):
            print('"{}" has no valid injection marker lines.'.format(
                exception.args[0]))
        if isinstance(exception, FileNotFoundError):
            print('Lacking resource "{}" to complete operation.'.format(
                exception.filename))
        if isinstance(exception, PermissionError):
            print('No write permission for current working directory.')
        if isinstance(exception, IsADirectoryError):
            print('"{}" is a directory. Provide a *.yaml scheme file instead.'
                  .format(exception.filename))

    elif mode == UPDATE_MODE_ID:
        if isinstance(exception, PermissionError):
            print('No write permission for current working directory.')
        if isinstance(exception, FileNotFoundError):
            print('Necessary resources for updating not found in current '
                  'working directory.')
    else:
        raise exception

    sys.exit(1)


def build_mode(arg_namespace):
    """Check command line arguments and run build function."""
    if count_arguments(arg_namespace.file, arg_namespace.custom):
        print('Non-build arguments ignored.')

    custom_temps = arg_namespace.template or []
    temp_paths = [rel_to_cwd('templates', temp) for temp in custom_temps]

    try:
        builder.build(templates=temp_paths,
                      schemes=arg_namespace.scheme,
                      base_output_dir=arg_namespace.output)
    except (LookupError, PermissionError) as exception:
        handle_exit_exception(BUILD_MODE_ID, exception)


def inject_mode(arg_namespace):
    """Check command line arguments and run build function."""
    if count_arguments(arg_namespace.template,
                       arg_namespace.output,
                       arg_namespace.custom):
        print('Non-inject arguments ignored.')

    if not arg_namespace.file or not arg_namespace.scheme:
        print('A scheme file and at least one injection file need to be '
              'provided.')
        sys.exit(1)

    # override multiple arguments here ([-1]) because we copied the scheme
    # option from the build operation
    try:
        injector.inject_into_files(arg_namespace.scheme[-1],
                                   arg_namespace.file)
    except (IndexError, FileNotFoundError,
            PermissionError, IsADirectoryError) as exception:
        handle_exit_exception(INJECT_MODE_ID, exception)


def update_mode(arg_namespace):
    """Check command line arguments and run update function."""
    if count_arguments(arg_namespace.file,
                       arg_namespace.scheme,
                       arg_namespace.template,
                       arg_namespace.output):
        print("Update operation doesn't allow for any arguments. Ignored.")
    else:
        try:
            updater.update(custom_sources=arg_namespace.custom)
        except (PermissionError, FileNotFoundError) as exception:
            handle_exit_exception(UPDATE_MODE_ID, exception)


def run():
    arg_namespace = argparser.parse_args()

    if arg_namespace.operation == 'update':
        update_mode(arg_namespace)
    elif arg_namespace.operation == 'build':
        build_mode(arg_namespace)
    elif arg_namespace.operation == 'inject':
        inject_mode(arg_namespace)


USAGE_STRING = '%(prog)s {update|build|inject} -t [...] -s [...] -f [...]'
DESC_STRING = '''
  update:   download all base16 scheme and template repositories
  build:    build base16 colorschemes from templates
  inject:   inject a colorscheme into one or multiple files
'''

desc_formatter = argparse.RawDescriptionHelpFormatter
argparser = argparse.ArgumentParser(usage=USAGE_STRING,
                                    description=DESC_STRING,
                                    formatter_class=desc_formatter)
update_group = argparser.add_argument_group('update arguments')
build_group = argparser.add_argument_group('build arguments')
inject_group = argparser.add_argument_group('inject arguments')
argparser.add_argument('operation', choices=['update', 'build', 'inject'],
                       metavar='type of operation', help=argparse.SUPPRESS)

update_group.add_argument('-c', '--custom', action='store_const', const=True,
                          help="""update repositories but don't update source
                          files""")

build_group.add_argument('-o', '--output', help='''specify a target directory
                         for the build output''')
build_group.add_argument('-t', '--template', action='append', metavar='TEMP',
                         help='''restrict operation to one or several templates
                         (must correspond to a directory in ./templates); can
                         be specified more than once''')
# use a different help text for scheme option depending on operational mode
s_option = build_group.add_argument('-s', '--scheme', action='append',
                                    help='''restrict operation to one or
                                    several schemes (must correspond
                                    to a yaml file in ./schemes/*/); can be
                                    specified more than once''')

inject_group.add_argument('-f', '--file', action='append', help='''provide
                          paths to files into which you wish to inject a
                          colorscheme; can be specified more than once''')
s2_option = copy(s_option)
s2_option.help = '''provide a path to the yaml scheme file which you wish to
                    inject'''
inject_group._group_actions.append(s2_option)
