import os
import shutil
import tempfile
import pytest
from pybase16_builder import shared, updater, builder, injector


@pytest.fixture(scope='module')
def clean_dir():
    """Remove all files/folders in the working dir that were not present before
    running the test."""
    orig_struct = os.listdir(shared.CWD)
    yield
    for file_ in os.listdir(shared.CWD):
        if file_ not in orig_struct:
            try:
                shutil.rmtree(file_)
            except NotADirectoryError:
                os.remove(file_)


@pytest.fixture(scope='function')
def clean_config():
    config = shared.rel_to_cwd(os.path.join('tests', 'test_config'))
    with open(config, 'r') as file_:
        orig_content = file_.read()
    yield config
    with open(config, 'w') as file_:
        file_.write(orig_content)


def test_update(clean_dir):
    updater.update()

    sources_path = shared.rel_to_cwd('sources.yaml')
    template_path = shared.rel_to_cwd('sources', 'templates', 'list.yaml')
    scheme_path = shared.rel_to_cwd('sources', 'schemes', 'list.yaml')
    directories = {sources_path: shared.rel_to_cwd('sources'),
                   template_path: shared.rel_to_cwd('templates'),
                   scheme_path: shared.rel_to_cwd('schemes')}

    # assume there's a corresponding git directory for every key in a yaml file
    for yaml_file, dir_ in directories.items():
        yaml_dict = shared.get_yaml_dict(yaml_file)
        for key in yaml_dict.keys():
            # assert there's a corresponding directory
            assert key in os.listdir(dir_)
            key_dir = os.path.join(dir_, key)
            # assert it's a git repo
            assert '.git' in os.listdir(key_dir)


def test_ressource_dirs(clean_dir):
    # assert there's a config.yaml for every template group
    for temp_path in builder.get_template_dirs():
        conf_path = shared.rel_to_cwd(temp_path, 'templates', 'config.yaml')
        assert os.path.exists(conf_path)

    # assert there's at least one yaml file for each scheme group
    for scheme_path in builder.get_scheme_dirs():
        yaml_glob = shared.rel_to_cwd(scheme_path, '*.yaml')
        assert len(yaml_glob) >= 1

    # assert get_scheme_files only returns yaml_files
    scheme_files = builder.get_scheme_files()
    for scheme_file in scheme_files:
        assert scheme_file[-5:] == '.yaml'


def test_build(clean_dir):
    builder.build()
    template_dirs = builder.get_template_dirs()
    templates = [builder.TemplateGroup(path) for path in template_dirs]
    for temp_group in templates:
        for temp, sub in temp_group.templates.items():
            output_dir = builder.rel_to_cwd('output', temp_group.name,
                                            sub['output'])
            # assert proper paths for each template were created
            assert os.path.exists(output_dir)
            # assert these directories aren't empty. so at least something
            # happened
            assert len(os.listdir(output_dir)) > 0


def test_custom_build(clean_dir):
    """Test building with specific parameters."""
    dunst_temp_path = shared.rel_to_cwd('templates', 'dunst')
    base_output_dir = tempfile.mktemp()
    builder.build(templates=[dunst_temp_path], schemes=['atelier-heath-light'],
                  base_output_dir=base_output_dir)

    dunst_temps = builder.TemplateGroup(dunst_temp_path).get_templates()
    # out_dirs = [dunst_temps[temp]['output'] for temp in dunst_temps.keys()]
    for temp, sub in dunst_temps.items():
        out_path = os.path.join(base_output_dir, 'dunst',
                                sub['output'])
        theme_file = 'base16-atelier-heath-light{}'.format(sub['extension'])
        out_file = os.path.join(out_path, theme_file)

        assert os.path.exists(out_file)
        assert len(os.listdir(out_path)) == 1


def test_inject(clean_config):
    """Test injection mode."""
    test_injection = 'TEST\nINJECT\nSTRING'
    rec = injector.Recipient(clean_config)
    assert rec.temp == 'i3##colors-only'

    # test colorscheme return
    test_scheme_path = shared.rel_to_cwd('tests', 'test_scheme.yaml')
    colorscheme = rec.get_colorscheme(test_scheme_path)
    assert colorscheme

    # test injection
    rec.inject_scheme(test_injection)
    rec.write()
    with open(clean_config) as file_:
        content = file_.read()
        matches = content.find(test_injection)
        assert matches > 0
