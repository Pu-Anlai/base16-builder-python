import os
import yaml

CWD = os.path.realpath(os.getcwd())


def rel_to_cwd(*args):
    """Get absolute real path of $path with $CWD as base."""
    return os.path.join(CWD, *args)


def get_yaml_dict(yaml_file):
    """Return a yaml_dict from reading yaml_file. If yaml_file is empty or
    doesn't exist, return an empty dict instead."""
    try:
        with open(yaml_file, 'r') as file_:
            yaml_dict = yaml.safe_load(file_.read()) or {}
        return yaml_dict
    except FileNotFoundError:
        return {}
