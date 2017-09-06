import yaml
import os

CWD = os.path.realpath(os.getcwd())


def rel_to_cwd(*args):
    """Get absolute real path of $path with $CWD as base."""
    return os.path.join(CWD, *args)


def get_yaml_dict(yaml_file):
    with open(yaml_file, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())
    return yaml_dict
