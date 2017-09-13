import os
import shutil
import pytest
import shared
import updater
import builder
import injector


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
    scheme_files = []
    for scheme_path in builder.get_scheme_dirs():
        scheme_files.extend(builder.get_scheme_files(scheme_path))
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


def test_inject():
    """Test injection mode."""
    test_injection = 'TEST\nINJECT\nSTRING'
    test_config = shared.rel_to_cwd(os.path.join('tests', 'text_config'))
    rec = injector.Recipient(test_config)
    assert rec.temp == 'i3##colors-only'
    rec.inject_scheme(test_injection)
    rec.write()
