base16-builder-python
================

Finally, a base16 builder that doesn't require me to install anything new.

Installation
------------
Testing is done with versions from Python 3.4 upward. Older versions might work as well, but Python 2 won't.
::
    pip install pybase16-builder

If you don't want to clutter your computer with something that you're just going to use once you can also just clone this repository and use the provided pybase16.py file.

Usage
-----
There are three modes of operation:
::
    pybase16 update
    pybase16 build
    pybase16 inject

Update
^^^^^^
Downloads all base16 schemes and templates to the current working directory.
The source files, i.e. the files pointing to the scheme and template repositories (see `here <https://github.com/chriskempson/base16/blob/master/builder.md>`_) will also be updated by default. If you want to use your own versions of these files (to exclude specific repositories, for example), you can prevent the builder from updating the source files by using the :code:`-c/--custom` option.

Build
^^^^^
Builds base16 colorschemes for all schemes and templates. This requires the directory structure and files created by the update operation to be present in the working directory. This operation accepts three parameters:

* :code:`-s/--scheme` restricts building to specific schemes

  Can be specified more than once. Each argument must correspond to a scheme file (sans extension).
* :code:`-t/--template` restricts building to specific templates

  Can be specified more than once. Each argument must correspond to a folder name in the templates directory.
* :code:`-o/--output` specifies a path where built colorschemes will be placed

  If this option is not specified, an "output" folder in the current working directory will be created and used.

Example:
::
    pybase16 build -t dunst -s atelier-heath-light -o /tmp/output

Inject
^^^^^^
This operation provides an easier way to quickly insert a specific colorscheme into one or more config files. It accepts two parameters:

* :code:`-s/--scheme` specifies the scheme you wish to injected

  This argument must be specified as a path to a yaml scheme file.

* :code:`-f/--file` specifies the file(s) into which you wish the scheme to be inserted

  Can be specified more than once. Each argument must be specified as a path to a config file that features proper injection markers (see below).

You will need to prepare your configuration files so that the script knows where to insert the colorscheme. This is done by including two lines in the file
::

    # %%base16_template: TEMPLATE_NAME##SUBTEMPLATE_NAME %%

    Everything in-between these two lines will be replaced with the colorscheme.

    # %%base16_template_end%%

Both lines can feature arbitrary characters before the first two percentage signs. This is so as to accomodate different commenting styles. Both lines need to end exactly as demonstrated above, however. The exception are "TEMPLATE_NAME" and "SUBTEMPLATE_NAME". Replace TEMPLATE_NAME with the name of the template you wish to insert, for example "gnome-terminal". As stated above, this must correspond to a folder in the templates directory. Replace SUBTEMPLATE_NAME with the name of the subtemplate as it is defined at the top level of the template's config.yaml file (see `here <https://github.com/chriskempson/base16/blob/master/file.md>`_ for details), for example "default-256". If you omit the subtemplate name (don't omit "##" though), "default" is assumed.

An example of an i3 config file prepared in such a way can be found `here <https://github.com/InspectorMustache/pybase16-builder/blob/master/tests/test_config>`_.

Provide a path to the colorscheme you wish to inject by pointing to its YAML file with the -s option. Use the -f option for each file into which you want to inject the scheme.

As an example, here's the command I use to globally change the color scheme in all applications that support it:
::
    pybase16 inject -s schemes/default/ocean.yaml -f ~/.gtkrc-2.0.mine -f ~/.config/dunst/dunstrc -f ~/.config/i3/config -f ~/.config/termite/config -f ~/.config/zathura/zathurarc
