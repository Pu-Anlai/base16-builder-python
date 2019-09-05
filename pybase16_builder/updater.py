import os
import sys
import subprocess
import shutil
import threading
from queue import Queue
from .shared import (get_yaml_dict, rel_to_cwd,
                     JobOptions, verb_msg, thread_print)


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


def initiate_job_options(**kwargs):
    """Return a JobOptions object."""
    return JobOptions(**kwargs)


def yaml_to_queue(yaml_file, base_dir):
    """Return a queues consisting of jobs made up of git repos from $yaml_file
    as well as their base target directory."""
    yaml_dict = get_yaml_dict(yaml_file)
    queue = Queue()
    for key, value in yaml_dict.items():
        queue.put((value, rel_to_cwd(base_dir, key)))

    return queue


def git_clone(git_url, path, job_options):
    """Clone git repository at $git_url to $path."""
    if os.path.exists(os.path.join(path, '.git')):
        # get rid of local repo if it already exists
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)
    thread_print(job_options.lock, 'Start cloning from {}…'.format(git_url),
                 verbose=job_options.verbose)
    my_env = os.environ.copy()
    my_env['GIT_TERMINAL_PROMPT'] = '0'
    git_proc = subprocess.Popen(['git', 'clone', git_url, path],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                env=my_env)

    try:
        stdoutmsg, stderrmsg = git_proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        git_proc.kill()
        stderrmsg = b'Timed out.'

    if git_proc.returncode == 0:
        thread_print(job_options.lock, 'Cloned {}.'.format(git_url),
                     verbose=job_options.verbose)
    else:
        err_msg = verb_msg(
            '{}:\n{}'.format(git_url, stderrmsg.decode('utf-8')), lvl=2)
        thread_print(job_options.lock, err_msg)


def git_clone_worker(queue, job_options):
    """Worker thread for picking up git clone jobs from $queue until it
    receives None."""
    while True:
        job = queue.get()
        if job is None:
            break
        git_url, path = job
        git_clone(git_url, path, job_options)
        queue.task_done()


def git_clone_from_job_options(queue, job_options):
    """Deal with all git clone jobs on $queue."""
    if queue.qsize() < 20:
        thread_num = queue.qsize()
    else:
        thread_num = 20

    threads = []
    for _ in range(thread_num):
        thread = threading.Thread(target=git_clone_worker,
                                  args=(queue, job_options))
        thread.start()
        threads.append(thread)

    queue.join()

    for _ in range(thread_num):
        queue.put(None)

    for thread in threads:
        thread.join()


def update(custom_sources=False, verbose=False):
    """Update function to be called from cli.py"""
    if not shutil.which('git'):
        print('Git executable not found in $PATH.')
        sys.exit(1)

    if not custom_sources:
        print('Creating sources.yaml…')
        write_sources_file()
        print('Cloning sources…')
        sources_file = rel_to_cwd('sources.yaml')
        queue = yaml_to_queue(sources_file, rel_to_cwd('sources'))
        job_options = initiate_job_options(verbose=verbose)
        git_clone_from_job_options(queue, job_options)

    print('Cloning templates…')
    queue = yaml_to_queue(rel_to_cwd('sources', 'templates', 'list.yaml'),
                          rel_to_cwd('templates'))
    job_options = initiate_job_options(verbose=verbose)
    git_clone_from_job_options(queue, job_options)

    print('Cloning schemes…')
    queue = yaml_to_queue(rel_to_cwd('sources', 'schemes', 'list.yaml'),
                          rel_to_cwd('schemes'))
    job_options = initiate_job_options(verbose=verbose)

    git_clone_from_job_options(queue, job_options)
    print('Completed updating repositories.')
