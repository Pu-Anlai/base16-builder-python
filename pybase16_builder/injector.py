import re
import pystache
from . import builder
from .shared import rel_to_cwd, get_yaml_dict

TEMP_NEEDLE = re.compile(r"^.*%%base16_template:([^%]+)%%$")
TEMP_END_NEEDLE = re.compile(r"^.*%%base16_template_end%%$")


class Recipient:
    """Represents a file into which a base16 scheme is to be injected."""

    def __init__(self, path):
        self.path = path
        self.content = self._get_file_content(self.path)
        self.temp = self._get_temp(self.content)

    def _get_file_content(self, path):
        """Return a string representation file content at $path."""
        with open(path, "r") as file_:
            content = file_.read()
        return content

    def _get_temp(self, content):
        """Get the string that points to a specific base16 scheme."""
        temp = None
        for line in content.split("\n"):

            # make sure there's both start and end line
            if not temp:
                match = TEMP_NEEDLE.match(line)
                if match:
                    temp = match.group(1).strip()
                    continue
            else:
                match = TEMP_END_NEEDLE.match(line)
                if match:
                    return temp

        raise IndexError(self.path)

    def get_colorscheme(self, scheme_file):
        """Return a string object with the colorscheme that is to be
        inserted."""
        scheme = get_yaml_dict(scheme_file)
        scheme_slug = builder.slugify(scheme_file)
        builder.format_scheme(scheme, scheme_slug)

        try:
            temp_base, temp_sub = self.temp.split("##")
        except ValueError:
            temp_base, temp_sub = (self.temp.strip("##"), "default")

        temp_path = rel_to_cwd("templates", temp_base)
        temp_group = builder.TemplateGroup(temp_path)
        try:
            single_temp = temp_group.templates[temp_sub]
        except KeyError:
            raise FileNotFoundError(None, None, self.path + " (sub-template)")

        colorscheme = pystache.render(single_temp["parsed"], scheme)
        return colorscheme

    def inject_scheme(self, b16_scheme):
        """Inject string $b16_scheme into self.content."""
        # correctly formatted start and end of block should have already been
        # ascertained by _get_temp
        content_lines = self.content.split("\n")
        b16_scheme_lines = b16_scheme.split("\n")
        start_line = None
        for num, line in enumerate(content_lines):
            if not start_line:
                match = TEMP_NEEDLE.match(line)
                if match:
                    start_line = num + 1
            else:
                match = TEMP_END_NEEDLE.match(line)
                if match:
                    end_line = num

        # put lines back together
        new_content_lines = (
            content_lines[0:start_line] + b16_scheme_lines + content_lines[end_line:]
        )
        self.content = "\n".join(new_content_lines)

    def write(self):
        """Write content back to file."""
        with open(self.path, "w") as file_:
            file_.write(self.content)


def inject_into_files(scheme, files):
    """Inject $scheme into list $files."""
    scheme_files = builder.get_scheme_files(scheme)
    if len(scheme_files) == 0:
        raise FileNotFoundError(None, None, scheme)
    if len(scheme_files) > 1:
        raise ValueError

    for file_ in files:
        rec = Recipient(file_)
        colorscheme = rec.get_colorscheme(*scheme_files)
        rec.inject_scheme(colorscheme)
        rec.write()
