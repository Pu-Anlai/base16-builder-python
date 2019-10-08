import os
import asyncio
import aiofiles
import pystache
from glob import glob
from .shared import get_yaml_dict, rel_to_cwd, JobOptions, verb_msg, compat_event_loop


class TemplateGroup(object):
    """Representation of a template group, i.e. a group of templates specified
    in a config.yaml."""

    def __init__(self, base_path):
        self.base_path = base_path
        self.name = os.path.basename(base_path.rstrip("/"))
        self.templates = self.get_templates()

    def get_templates(self):
        """
        Return a list of template_dicts based on the config.yaml in
        $self.base_path. Keys correspond to templates and values represent
        further settings regarding each template. A pystache object containing
        the parsed corresponding mustache file is added to the sub-dictionary.
        """
        config_path = rel_to_cwd(self.base_path, "templates", "config.yaml")
        templates = get_yaml_dict(config_path)
        for temp, sub in templates.items():
            mustache_path = os.path.join(
                get_parent_dir(config_path), "{}.mustache".format(temp)
            )
            sub["parsed"] = get_pystache_parsed(mustache_path)
        return templates


def get_parent_dir(base_dir, level=1):
    "Get the directory $level levels above $base_dir."
    while level > 0:
        base_dir = os.path.dirname(base_dir)
        level -= 1
    return base_dir


def get_pystache_parsed(mustache_file):
    """Return a ParsedTemplate instance based on the contents of
    $mustache_file."""
    with open(mustache_file, "r") as file_:
        parsed = pystache.parse(file_.read())
    return parsed


def get_template_dirs():
    """Return a set of all template directories."""
    temp_glob = rel_to_cwd("templates", "**", "templates", "config.yaml")
    temp_groups = glob(temp_glob)
    temp_groups = [get_parent_dir(path, 2) for path in temp_groups]
    return set(temp_groups)


def get_scheme_dirs():
    """Return a set of all scheme directories."""
    scheme_glob = rel_to_cwd("schemes", "**", "*.yaml")
    scheme_groups = glob(scheme_glob)
    scheme_groups = [get_parent_dir(path) for path in scheme_groups]
    return set(scheme_groups)


def get_scheme_files(patterns=None):
    """Return a list of all (or those matching $pattern) yaml (scheme)
    files."""
    patterns = patterns or ["*"]
    pattern_list = ["{}.yaml".format(pattern) for pattern in patterns]
    scheme_files = []
    for scheme_path in get_scheme_dirs():
        for pattern in pattern_list:
            file_paths = glob(os.path.join(scheme_path, pattern))
            scheme_files.extend(file_paths)

    return scheme_files


def reverse_hex(hex_str):
    """Reverse a hex foreground string into its background version."""
    hex_str = "".join([hex_str[i : i + 2] for i in range(0, len(hex_str), 2)][::-1])
    return hex_str


def format_scheme(scheme, slug):
    """Change $scheme so it can be applied to a template."""
    scheme["scheme-name"] = scheme.pop("scheme")
    scheme["scheme-author"] = scheme.pop("author")
    scheme["scheme-slug"] = slug
    bases = ["base{:02X}".format(x) for x in range(0, 16)]
    for base in bases:
        scheme["{}-hex".format(base)] = scheme.pop(base)
        scheme["{}-hex-r".format(base)] = scheme["{}-hex".format(base)][0:2]
        scheme["{}-hex-g".format(base)] = scheme["{}-hex".format(base)][2:4]
        scheme["{}-hex-b".format(base)] = scheme["{}-hex".format(base)][4:6]
        scheme["{}-hex-bgr".format(base)] = reverse_hex(scheme["{}-hex".format(base)])

        scheme["{}-rgb-r".format(base)] = str(int(scheme["{}-hex-r".format(base)], 16))
        scheme["{}-rgb-g".format(base)] = str(int(scheme["{}-hex-g".format(base)], 16))
        scheme["{}-rgb-b".format(base)] = str(int(scheme["{}-hex-b".format(base)], 16))

        scheme["{}-dec-r".format(base)] = str(
            int(scheme["{}-rgb-r".format(base)]) / 255
        )
        scheme["{}-dec-g".format(base)] = str(
            int(scheme["{}-rgb-g".format(base)]) / 255
        )
        scheme["{}-dec-b".format(base)] = str(
            int(scheme["{}-rgb-b".format(base)]) / 255
        )


def slugify(scheme_file):
    """Format $scheme_file_name to be used as a slug variable."""
    scheme_file_name = os.path.basename(scheme_file)
    if scheme_file_name.endswith(".yaml"):
        scheme_file_name = scheme_file_name[:-5]
    return scheme_file_name.lower().replace(" ", "-")


async def build_single(scheme_file, job_options):
    """Build colorscheme from $scheme_file using $job_options. Return True if
    completed without warnings. Otherwise false."""
    scheme = get_yaml_dict(scheme_file)
    scheme_slug = slugify(scheme_file)
    format_scheme(scheme, scheme_slug)
    scheme_name = scheme["scheme-name"]
    warn = False  # set this for feedback to the caller

    if job_options.verbose:
        print('Building colorschemes for scheme "{}"...'.format(scheme_name))

    for temp_group in job_options.templates:

        for _, sub in temp_group.templates.items():
            output_dir = os.path.join(
                job_options.base_output_dir, temp_group.name, sub["output"]
            )
            try:
                os.makedirs(output_dir)
            except FileExistsError:
                pass

            if sub["extension"] is not None:
                filename = "base16-{}{}".format(scheme_slug, sub["extension"])
            else:
                filename = "base16-{}".format(scheme_slug)

            build_path = os.path.join(output_dir, filename)

            # include a warning for files being overwritten to comply with
            # base16 0.9.1
            if os.path.isfile(build_path):
                verb_msg("File {} exists and will be overwritten.".format(build_path))
                warn = True

            async with aiofiles.open(build_path, "w") as file_:
                file_content = pystache.render(sub["parsed"], scheme)
                await file_.write(file_content)

            if job_options.verbose:
                print('Built colorschemes for scheme "{}".'.format(scheme_name))

    return not (warn)


async def build_single_task(scheme_file, job_options):
    """Worker thread for picking up scheme files from $queue and building b16
    templates using $templates until it receives None."""
    try:
        return await build_single(scheme_file, job_options)
    except Exception as e:
        verb_msg("{}: {!s}".format(scheme_file, e), lvl=2)
        return False


async def build_scheduler(scheme_files, job_options):
    """Create a task list from scheme_files and run tasks asynchronously."""
    task_list = [build_single_task(f, job_options) for f in scheme_files]
    return await asyncio.gather(*task_list)


def build(templates=None, schemes=None, base_output_dir=None, verbose=False):
    """Main build function to initiate building process."""
    template_dirs = templates or get_template_dirs()
    scheme_files = get_scheme_files(schemes)
    base_output_dir = base_output_dir or rel_to_cwd("output")

    # raise LookupError if there is not at least one template or scheme
    # to work with
    if not template_dirs or not scheme_files:
        raise LookupError

    # raise PermissionError if user has no write acces for $base_output_dir
    try:
        os.makedirs(base_output_dir)
    except FileExistsError:
        pass

    if not os.access(base_output_dir, os.W_OK | os.X_OK):
        raise PermissionError

    templates = [TemplateGroup(path) for path in template_dirs]

    job_options = JobOptions(
        base_output_dir=base_output_dir, templates=templates, verbose=verbose
    )

    with compat_event_loop() as event_loop:
        results = event_loop.run_until_complete(
            build_scheduler(scheme_files, job_options)
        )

    print("Finished building process.")
    return all(results)
