import yaml
import os
import subprocess
import shutil
from threading import Thread
from queue import Queue

CWD = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


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
        job_list.append((value, os.path.join(CWD, base_dir, key)))

    git_clone_all(job_list)


def git_clone(git_url, path):
    """Clone git repository at $git_url to $path."""
    if os.path.exists(os.path.join(path, '.git')):
        # get rid of local repo if it already exists
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)
    git_proc = subprocess.run(['git', 'clone', git_url, path],
                              stderr=subprocess.PIPE)
    if git_proc.returncode == 0:
        print('Cloned {}.'.format(git_url))
    else:
        errmsg = git_proc.stderr.decode('utf-8')
        print('Error cloning from {}:\n{}'.format(git_url,
                                                  errmsg))


def git_clone_worker(queue):
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
    for _ in range(50):
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
    download_from_yaml(os.path.join(CWD, 'sources.yaml'),
                       os.path.join(CWD, 'sources'))
    print('Cloning templates…')
    download_from_yaml(os.path.join(CWD, 'sources', 'templates', 'list.yaml'),
                       os.path.join(CWD, 'templates'))
    print('Cloning schemes…')
    download_from_yaml(os.path.join(CWD, 'sources', 'schemes', 'list.yaml'),
                       os.path.join(CWD, 'schemes'))
