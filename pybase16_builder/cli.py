import sys
import argparse
from . import updater, builder, injector
from .shared import rel_to_cwd


def count_arguments(*args):
    """Takes in argument attributes from an argparse Namespace object and
    counts how many of them are not None."""
    arg_count = len([x for x in args if x is not None])
    return arg_count


def update_mode(arg_namespace):
    """Check command line arguments and run update function."""
    if count_arguments(arg_namespace.file,
                       arg_namespace.scheme,
                       arg_namespace.template):
        print("Update operation doesn't allow for any arguments. Ignored.")
    else:
        try:
            updater.update()
        except PermissionError:
            print("No write permission for current working directory.")
            sys.exit(1)


def build_mode(arg_namespace):
    """Check command line arguments and run build function."""
    if count_arguments(arg_namespace.file, arg_namespace.scheme):
        print('Inject arguments ignored.')

    custom_temps = arg_namespace.template or []
    temp_paths = [rel_to_cwd('templates', temp) for temp in custom_temps]

    try:
        builder.build(templates=temp_paths)
    except (builder.ResourceError, PermissionError) as exception:
        if isinstance(exception, builder.ResourceError):
            print('Necessary resources for building not found in current '
                  'working directory.')
        if isinstance(exception, PermissionError):
            print("No write permission for current working directory.")

        sys.exit(1)


def inject_mode(arg_namespace):
    """Check command line arguments and run build function."""
    if count_arguments(arg_namespace.template):
        print('Build arguments ignored.')

    if not arg_namespace.file or not arg_namespace.scheme:
        print('A scheme file and at least one injection file need to be '
              'provided.')
        sys.exit(1)

    injector.inject_into_files(arg_namespace.scheme,
                               arg_namespace.file)


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
build_group = argparser.add_argument_group('build arguments')
inject_group = argparser.add_argument_group('inject arguments')
argparser.add_argument('operation', choices=['update', 'build', 'inject'],
                       metavar='type of operation', help=argparse.SUPPRESS)

build_group.add_argument('-t', '--template', action='append', metavar='TEMP',
                         help='''restrict operation to one or several templates
                         (must correspond to a directory in ./templates); can
                         be specified more than once''')

inject_group.add_argument('-f', '--file', action='append', help='''provide
                          paths to files into which you wish to inject a
                          colorscheme; can be specified more than once''')
inject_group.add_argument('-s', '--scheme', help='''provide a path to the
                          yaml scheme file which you wish to inject''')

if __name__ == '__main__':
    run()
