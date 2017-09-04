import updater
import builder
import shared
import pytest
import os
import shutil
import glob


@pytest.fixture(scope='module')
def clean_dir():
    """Remove all files/folders in the working dir that were not present before
    running the test."""
    orig_struct = os.listdir(shared.CWD)
    yield
    for file_ in os.listdir(shared.CWD):
        if file_ not in orig_struct:
            shutil.rmtree(file_)


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


def test_build():
    scheme_file = shared.rel_to_cwd('schemes', 'dracula', 'dracula.yaml')
    template_dirs = builder.get_template_dirs()
    templates = [builder.TemplateGroup(path) for path in template_dirs]
    builder.build_single(scheme_file, templates)
