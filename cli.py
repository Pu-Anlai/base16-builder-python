import argparse
import updater
import builder
import sys
from shared import rel_to_cwd


def get_optionals(args):
    """Return a list of all optional arguments from an argparse Namespace
    object."""
    optionals = []
    for arg in args.template, args.file, args.scheme:
        if arg is None:
            pass
        elif type(arg) is list:
            optionals.extend(arg)
        else:
            optionals.append(arg)

    return optionals


usage_string = '%(prog)s {update|build|inject} -t [...] -s [...] -f [...]'
desc_string = '''
  update:   download all base16 scheme and template repositories
  build:    build base16 colorschemes from templates
  inject:   inject a colorscheme into one or multiple files

build arguments:
  -t, --template [...]
    restrict operation to one or several templates (must correspond to a
    directory in ./templates)
    can be specified more than once

inject arguments:
  -f, --file [...]
    provide paths to files into which you wish to inject a colorscheme
    can be specified more than once
  -s, --scheme [...]
    provide a path to the mustache file of the scheme which you wish to inject
'''

argparser = argparse.ArgumentParser(
        usage=usage_string,
        description=desc_string,
        formatter_class=argparse.RawDescriptionHelpFormatter
        )
argparser.add_argument('operation', choices=['update', 'build', 'inject'],
                       metavar='type of operation', help=argparse.SUPPRESS)
argparser.add_argument('-t', '--template', action='append', metavar='TEMP',
                       help=argparse.SUPPRESS)
argparser.add_argument('-f', '--file', action='append', help=argparse.SUPPRESS)
argparser.add_argument('-s', '--scheme', help=argparse.SUPPRESS)

if __name__ == '__main__':
    args = argparser.parse_args()

    if args.operation == 'update':
        if len(get_optionals(args)) > 0:
            print("Update operation doesn't allow for any arguments.")
            print(get_optionals(args))
            sys.exit(1)
        else:
            updater.update()

    elif args.operation == 'build':
        # TODO: check for valid paths in builder.py
        custom_temps = args.template or []
        temp_paths = [rel_to_cwd('templates', temp) for temp in custom_temps]
        builder.build(templates=temp_paths)

    elif args.operation == 'inject':
        pass
