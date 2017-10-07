import os
import sys
import subprocess
import shutil
from threading import Thread
from queue import Queue
from .shared import get_yaml_dict, rel_to_cwd


def write_sources_file():
    """Write a sources.yaml file to current working dir."""
    file_content = (
        'schemes: '
        'https://github.com/chriskempson/base16-schemes-source.git\n'
        'templates: '
        'https://github.com/chriskempson/base16-templates-source.git'
    )
    file_path = rel_to_cwd('sources.yaml')
    with open(file_path, 'w') as file_:
        file_.write(file_content)


def yaml_to_job_list(yaml_file, base_dir):
    """Return a job_list consisting of git repos from $yaml_file as well as
    their base target directory."""
    yaml_dict = get_yaml_dict(yaml_file)
    job_list = []
    for key, value in yaml_dict.items():
        job_list.append((value, rel_to_cwd(base_dir, key)))

    return job_list


def git_clone(git_url, path):
    """Clone git repository at $git_url to $path."""
    if os.path.exists(os.path.join(path, '.git')):
        # get rid of local repo if it already exists
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)
    print('Start cloning from {}…'.format(git_url))
    git_proc = subprocess.Popen(['git', 'clone', git_url, path],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                env={'GIT_TERMINAL_PROMPT': '0'})

    try:
        stdoutmsg, stderrmsg = git_proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        git_proc.kill()
        stderrmsg = b'Timed out.'

    if git_proc.returncode == 0:
        print('Cloned {}.'.format(git_url))
    else:
        print('Error cloning from {}:\n{}'.format(git_url,
                                                  stderrmsg.decode('utf-8')))


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


def git_clone_job_list(job_list):
    """Deal with all git clone jobs in $job_list."""
    queue = Queue()
    for job in job_list:
        queue.put(job)

    if len(job_list) < 20:
        thread_num = len(job_list)
    else:
        thread_num = 20

    threads = []
    for _ in range(thread_num):
        thread = Thread(target=git_clone_worker, args=(queue, ))
        thread.start()
        threads.append(thread)

    queue.join()

    for _ in range(thread_num):
        queue.put(None)

    for thread in threads:
        thread.join()


def update(custom_sources=False):
    """Update function to be called from cli.py"""
    if not shutil.which('git'):
        print('Git executable not found in $PATH.')
        sys.exit(1)

    if not custom_sources:
        print('Creating sources.yaml…')
        write_sources_file()
        print('Cloning sources…')
        sources_file = rel_to_cwd('sources.yaml')
        jobs = yaml_to_job_list(sources_file, rel_to_cwd('sources'))
        git_clone_job_list(jobs)

    print('Cloning templates…')
    jobs = yaml_to_job_list(rel_to_cwd('sources', 'templates', 'list.yaml'),
                            rel_to_cwd('templates'))
    print('Cloning schemes…')
    jobs.extend(yaml_to_job_list(rel_to_cwd('sources', 'schemes', 'list.yaml'),
                                 rel_to_cwd('schemes')))
    git_clone_job_list(jobs)
    print('Completed updating repositories.')
