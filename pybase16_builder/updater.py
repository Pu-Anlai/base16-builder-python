import os
import sys
import shutil
import asyncio
from .shared import get_yaml_dict, rel_to_cwd, verb_msg, compat_event_loop


def write_sources_file():
    """Write a sources.yaml file to current working dir."""
    file_content = (
        "schemes: "
        "https://github.com/chriskempson/base16-schemes-source.git\n"
        "templates: "
        "https://github.com/chriskempson/base16-templates-source.git"
    )
    file_path = rel_to_cwd("sources.yaml")
    with open(file_path, "w") as file_:
        file_.write(file_content)


async def git_clone(git_url, path, verbose=False):
    """Clone git repository at $git_url to $path. Return True if succesful,
    otherwise False."""
    if verbose:
        print("Cloning {}...".format(git_url))
    if os.path.exists(os.path.join(path, ".git")):
        # get rid of local repo if it already exists
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)

    proc_env = os.environ.copy()
    proc_env["GIT_TERMINAL_PROMPT"] = "0"
    git_proc = await asyncio.create_subprocess_exec(
        "git", "clone", git_url, path, stderr=asyncio.subprocess.PIPE, env=proc_env
    )
    stdout, stderr = await git_proc.communicate()

    if git_proc.returncode != 0:
        # remove created directory if it's empty
        try:
            os.rmdir(path)
        except OSError:
            pass

        verb_msg("{}:\n{}".format(git_url, stderr.decode("utf-8")))
        return False
    elif verbose:
        print("Cloned {}".format(git_url))
    return True


async def git_clone_scheduler(yaml_file, base_dir, verbose=False):
    """Create task list for clone jobs and run them asynchronously."""
    jobs = generate_jobs_from_yaml(yaml_file, base_dir)
    task_list = [git_clone(*args_, verbose=verbose) for args_ in jobs]
    return await asyncio.gather(*task_list)


def generate_jobs_from_yaml(yaml_file, base_dir):
    yaml_dict = get_yaml_dict(yaml_file)
    for key, value in yaml_dict.items():
        yield (value, rel_to_cwd(base_dir, key))


def update(custom_sources=False, verbose=False):
    """Update function to be called from cli.py"""
    if not shutil.which("git"):
        print("Git executable not found in $PATH.")
        sys.exit(1)

    results = []
    with compat_event_loop() as event_loop:
        if not custom_sources:
            print("Creating sources.yaml…")
            write_sources_file()

        print("Cloning sources…")
        sources_file = rel_to_cwd("sources.yaml")
        r = event_loop.run_until_complete(
            git_clone_scheduler(
                sources_file, rel_to_cwd("sources"), verbose=verbose
            )
        )
        results.append(r)

        print("Cloning templates…")
        r = event_loop.run_until_complete(
            git_clone_scheduler(
                rel_to_cwd("sources", "templates", "list.yaml"),
                rel_to_cwd("templates"),
                verbose=verbose,
            )
        )
        results.append(r)

        print("Cloning schemes…")
        r = event_loop.run_until_complete(
            git_clone_scheduler(
                rel_to_cwd("sources", "schemes", "list.yaml"),
                rel_to_cwd("schemes"),
                verbose=verbose,
            )
        )
        results.append(r)

    return all(results)
