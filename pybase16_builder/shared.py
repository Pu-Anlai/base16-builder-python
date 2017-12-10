import os
import yaml

CWD = os.path.realpath(os.getcwd())


def rel_to_cwd(*args):
    """Get absolute real path of $path with $CWD as base."""
    return os.path.join(CWD, *args)


def get_yaml_dict(yaml_file):
    with open(yaml_file, 'r') as file_:
        yaml_dict = yaml.safe_load(file_.read())
    return yaml_dict
