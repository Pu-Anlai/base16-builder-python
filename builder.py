import yaml
import os
import subprocess
import shutil
from threading import Thread
from queue import Queue

CWD = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def rel_to_cwd(*args):
    """Get absolute real path of $path with $CWD as base."""
    return os.path.join(CWD, *args)


def get_yaml_dict(yaml_file):
    with open(yaml_file, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())

    return yaml_dict


def download_from_yaml(yaml_file, base_dir):
    """Take every value in $yaml_file as a git url and clone it to a directory
    of the same name as the corresponding key within $base_dir."""
    yaml_dict = get_yaml_dict(yaml_file)
    job_list = []
    for key, value in yaml_dict.items():
        job_list.append((value, rel_to_cwd(base_dir, key)))

    git_clone_all(job_list)


def git_clone(git_url, path):
    """Clone git repository at $git_url to $path."""
    if os.path.exists(os.path.join(path, '.git')):
        # get rid of local repo if it already exists
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)
    print('Start cloning from {}…'.format(git_url))
    git_proc = subprocess.run(['git', 'clone', git_url, path],
                              stderr=subprocess.PIPE)
    if git_proc.returncode == 0:
        print('Cloned {}.'.format(git_url))
    else:
        errmsg = git_proc.stderr.decode('utf-8')
        print('Error cloning from {}:\n{}'.format(git_url,
                                                  errmsg))


def git_clone_worker(queue):
    """Worker thread for picking up git clone jobs from $queue until it
    receives None."""
    while True:
        job = queue.get()
        if job is None:
            break
        git_url, path = job
        git_clone(git_url, path)
        queue.task_done()


def git_clone_all(job_list):
    """Run git_clone for every job in $job_list. Every job is represented as a
    tuple that unpacks to git_url + path."""
    queue = Queue()
    for job in job_list:
        queue.put(job)

    threads = []
    for _ in range(40):
        thread = Thread(target=git_clone_worker, args=(queue, ))
        thread.start()
        threads.append(thread)

    queue.join()

    for job in range(50):
        queue.put(None)

    for thread in threads:
        thread.join()


def update():
    print('Cloning sources…')
    download_from_yaml(rel_to_cwd('sources.yaml'),
                       rel_to_cwd('sources'))
    print('Cloning templates…')
    download_from_yaml(rel_to_cwd('sources', 'templates', 'list.yaml'),
                       rel_to_cwd('templates'))
    print('Cloning schemes…')
    download_from_yaml(rel_to_cwd('sources', 'schemes', 'list.yaml'),
                       rel_to_cwd('schemes'))
    print('Completed updating repositories.')
