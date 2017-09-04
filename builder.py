import os
import glob
import shutil
import pystache
from shared import get_yaml_dict, rel_to_cwd


class TemplateGroup(object):
    """Representation of a template."""

    def __init__(self, base_path):
        self.base_path = base_path
        self.name = os.path.basename(base_path)
        self.templates = self.get_templates()

    def get_templates(self):
        """Return a list of template_dicts."""
        config_path = rel_to_cwd(self.base_path, 'templates', 'config.yaml')
        templates = get_yaml_dict(config_path)
        for temp, sub in templates.items():
            mustache_path = os.path.join(get_parent_dir(config_path),
                                         f'{temp}.mustache')
            sub['parsed'] = get_pystache_parsed(mustache_path)
        return templates


def transform_template(scheme, template):
    """Apply $scheme to $template and return the result string."""
    result = pystache.render(template, scheme)
    return result


def get_parent_dir(base_dir, level=1):
    "Get the directory $level levels above $base_dir."
    while level > 0:
        base_dir = os.path.dirname(base_dir)
        level -= 1
    return base_dir


def get_pystache_parsed(mustache_file):
    """Return a ParsedTemplate instance based on the contents of
    $mustache_file."""
    with open(mustache_file, 'r') as file_:
        parsed = pystache.parse(file_.read())
    return parsed


def get_template_dirs():
    """Return a list of all templates."""
    temp_glob = rel_to_cwd('templates', '**', 'templates', 'config.yaml')
    temp_groups = glob.glob(temp_glob)
    temp_groups = [get_parent_dir(path, 2) for path in temp_groups]
    return temp_groups


def get_scheme_dirs():
    scheme_glob = rel_to_cwd('schemes', '**', '*.yaml')
    scheme_groups = glob.glob(scheme_glob)
    scheme_groups = [get_parent_dir(path) for path in scheme_groups]
    return scheme_groups


def get_scheme_files(path):
    """Return a list of all $yaml (scheme) files in $path."""
    scheme_glob = os.path.join(path, '*.yaml')
    return glob.glob(scheme_glob)


def format_scheme(scheme, slug):
    """Change $scheme so it can be applied to a template."""
    scheme['scheme-name'] = scheme.pop('scheme')
    scheme['scheme-author'] = scheme.pop('author')
    scheme['scheme-slug'] = slug
    bases = ['base{:02X}'.format(x) for x in range(0, 16)]
    for base in bases:
        scheme[f'{base}-hex'] = scheme.pop(base)
        scheme[f'{base}-hex-r'] = scheme[f'{base}-hex'][0:2]
        scheme[f'{base}-hex-g'] = scheme[f'{base}-hex'][2:4]
        scheme[f'{base}-hex-b'] = scheme[f'{base}-hex'][4:6]

        scheme[f'{base}-rgb-r'] = str(int(scheme[f'{base}-hex-r'], 16))
        scheme[f'{base}-rgb-g'] = str(int(scheme[f'{base}-hex-g'], 16))
        scheme[f'{base}-rgb-b'] = str(int(scheme[f'{base}-hex-b'], 16))

        scheme[f'{base}-dec-r'] = str(int(scheme[f'{base}-rgb-r']) / 255)
        scheme[f'{base}-dec-g'] = str(int(scheme[f'{base}-rgb-g']) / 255)
        scheme[f'{base}-dec-b'] = str(int(scheme[f'{base}-rgb-b']) / 255)


def slugify(scheme_file_name):
    """Format $scheme_file_name to be used as a slug variable."""
    if scheme_file_name.endswith('.yaml'):
        scheme_file_name = scheme_file_name[:-5]
    return scheme_file_name.lower().replace(' ', '-')


def build_single(scheme_file, templates):
    """Build colorscheme for a single $scheme_file using all TemplateGroup
    instances in $templates."""
    scheme = get_yaml_dict(scheme_file)
    scheme_slug = slugify(os.path.basename(scheme_file))
    format_scheme(scheme, scheme_slug)

    for temp_group in templates:

        for temp, sub in temp_group.templates.items():
            output_dir = rel_to_cwd('output', temp_group.name,
                                    sub['output'])
            try:
                os.makedirs(output_dir)
            except FileExistsError:
                shutil.rmtree(output_dir)
                os.makedirs(output_dir)

            filename = 'base16-{}{}'.format(scheme_slug, sub['extension'])
            build_path = os.path.join(output_dir, filename)
            with open(build_path, 'w') as file_:
                file_content = pystache.render(sub['parsed'], scheme)
                file_.write(file_content)


def build(schemes=None, templates=None):
    scheme_dirs = schemes or get_scheme_dirs()
    template_dirs = templates or get_template_dirs()

    scheme_files = [get_scheme_files(path) for path in scheme_dirs]
    templates = [TemplateGroup(path) for path in template_dirs]
