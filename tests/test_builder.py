import builder
import pytest
import os
import shutil


@pytest.fixture(scope='module')
def clean_dir():
    """Remove all files/folders in the working dir that were not present before
    running the test."""
    orig_struct = os.listdir(builder.CWD)
    yield
    for file_ in os.listdir(builder.CWD):
        if file_ not in orig_struct:
            shutil.rmtree(file_)


def test_update(clean_dir):
    builder.update()

    sources_path = builder.rel_to_cwd('sources.yaml')
    template_path = builder.rel_to_cwd('sources', 'templates', 'list.yaml')
    scheme_path = builder.rel_to_cwd('sources', 'schemes', 'list.yaml')
    directories = {sources_path: builder.rel_to_cwd('sources'),
                   template_path: builder.rel_to_cwd('templates'),
                   scheme_path: builder.rel_to_cwd('schemes')}

    # assume there's a corresponding directory for every key in a yaml file
    for yaml_file, dir_ in directories.items():
        yaml_dict = builder.get_yaml_dict(yaml_file)
        for key in yaml_dict.keys():
            assert key in os.listdir(dir_)
