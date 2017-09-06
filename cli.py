import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument('operation', choices=['update', 'build', 'inject'])
argparser.add_argument('-t', '--template', nargs='+', metavar='DIR',
                       help='''restrict operation to one or more templates; the
                       specified templates must correspond to the name of a
                       directory in the templates directory''')
argparser.epilog = "'--' can be used to separate arguments"

if __name__ == '__main__':
    print('bli')
    args = argparser.parse_args()
