.. image:: https://travis-ci.org/InspectorMustache/base16-builder-python.svg?branch=master
   :target: https://travis-ci.org/InspectorMustache/base16-builder-python

base16-builder-python
=====================

Finally, a base16 builder that doesn't require me to install anything new.

Installation
------------
As this project uses async/await syntax, the lowest supported Python version is 3.5.
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

Basic Usage
^^^^^^^^^^^
If you just want to build all base16 colorschemes and then pick out the ones you need, simply run:
::

   pybase16 update
   pybase16 build

Once the process is finished, you can find all colorschemes in a folder named output located in the current working directory.

For a more detailed explanation of the individual commands, read on.

Update
^^^^^^
Downloads all base16 schemes and templates to the current working directory.
The source files, i.e. the files pointing to the scheme and template repositories (see `builder.md <https://github.com/chriskempson/base16/blob/master/builder.md>`_) will also be updated by default.  If you want to use your own versions of these files (to exclude specific repositories, for example), you can prevent the builder from updating the source files by using the :code:`-c/--custom` option.
You can use :code:`-v/--verbose` for more detailed output.

Build
^^^^^
Builds base16 colorschemes for all schemes and templates.  This requires the directory structure and files created by the update operation to be present in the working directory.  This operation accepts four parameters:

* :code:`-s/--scheme` restricts building to specific schemes

  Can be specified more than once.  Each argument must match a scheme.  Wildcards can be used but must be escaped properly so they are not expanded by the shell.

* :code:`-t/--template` restricts building to specific templates

  Can be specified more than once.  Each argument must correspond to a folder name in the templates directory.

* :code:`-o/--output` specifies a path where built colorschemes will be placed

  If this option is not specified, an "output" folder in the current working directory will be created and used.

* :code:`-v/--verbose` increases verbosity

  With this option specified the builder prints out the name of each scheme as it's built.

Example:
::

    pybase16 build -t dunst -s atelier-heath-light -o /tmp/output

Inject
^^^^^^
This operation provides an easier way to quickly insert a specific colorscheme into one or more config files.  In order for the builder to locate the necessary files, this command relies on the folder structure created by the update command.  The command accepts two parameters:

* :code:`-s/--scheme` specifies the scheme you wish to inject

  Refers to the scheme that should be inserted.  You can use wildcards and the same restrictions as with update apply.  A pattern that matches more than one scheme will cause an error.

* :code:`-f/--file` specifies the file(s) into which you wish the scheme to be inserted

  Can be specified more than once.  Each argument must be specified as a path to a config file that features proper injection markers (see below).

You will need to prepare your configuration files so that the script knows where to insert the colorscheme.  This is done by including two lines in the file
::

    # %%base16_template: TEMPLATE_NAME##SUBTEMPLATE_NAME %%

    Everything in-between these two lines will be replaced with the colorscheme.

    # %%base16_template_end%%

Both lines can feature arbitrary characters before the first two percentage signs.  This is so as to accomodate different commenting styles.  Both lines need to end exactly as demonstrated above, however.  "TEMPLATE_NAME" and "SUBTEMPLATE_NAME" are the exception to this.  Replace TEMPLATE_NAME with the name of the template you wish to insert, for example "gnome-terminal".  This must correspond to a folder in the templates directory.  Replace SUBTEMPLATE_NAME with the name of the subtemplate as it is defined at the top level of the template's config.yaml file (see `file.md <https://github.com/chriskempson/base16/blob/master/file.md>`_ for details), for example "default-256".  If you omit the subtemplate name (don't omit "##" though), "default" is assumed.

An example of an i3 config file prepared in such a way can be found `here <https://github.com/InspectorMustache/pybase16-builder/blob/master/tests/test_config>`_.

Specify the name of the scheme you wish to inject with the -s option.  Use the -f option for each file into which you want to inject the scheme.

As an example, here's the command I use to globally change the color scheme in all applications that support it:
::

    pybase16 inject -s ocean -f ~/.gtkrc-2.0.mine -f ~/.config/dunst/dunstrc -f ~/.config/i3/config -f ~/.config/termite/config -f ~/.config/zathura/zathurarc

Exit
^^^^
The program exits with exit code 1 if it encountered a general error and with 2 if one or more build or update tasks produced a warning or an error.
