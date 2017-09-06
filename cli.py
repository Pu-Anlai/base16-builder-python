import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument('command', choices=['update', 'build', 'inject'])
argparser.add_argument('-t',
                       help='restrict operation to one or more templates')
args = argparser.parse_args()
print(args.command)
