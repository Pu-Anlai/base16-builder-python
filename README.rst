pybase16-builder
================

Finally, a base16 builder that doesn't require me to install anything new.

Installation
------------
You need at least Python 3.6 because I like f-strings.
::
    pip install pybase16-builder

If you don't want to clutter your computer with something that you're probably just going to use once you can also just clone this repository and use the provided pybase16.py file.

Usage
-----
There are three modes of operations::
    pybase16 update
    pybase16 build
    pybase16 inject

Update
^^^^^^
Downloads all base16 schemes and templates to the current working directory.

Build
^^^^^
Builds base16 colorschemes for all schemes and templates. The built colorschemes are put into a folder called output in the current working directory. You can also limit building to certain templates with the -t option (cf. `pybase16 -h`) if you really need those colorschemes and can't wait an additional 8 seconds or so. The parameters that are specified with -t must correspond to a folder in the templates directory (which is created by the update operation).

Inject
^^^^^^
This operation provides an easier way to quickly insert a specific colorscheme into one or more config files. You need to prepare your configuration files so that the script knows where to insert the colorscheme. This is done by including two lines in the file::

    # %%base16_template: TEMPLATE_NAME##SUBTEMPLATE_NAME %%

    Everything in-between these two lines will be replace with the colorscheme.

    # %%base16_template_end%%

Both lines can feature arbitrary characters before the two percentage signs. This is done to accomodate different comment styles. Both lines need to end exactly as demonstrated above, however. Replace TEMPLATE_NAME with the name of the template you wish to insert (for example "gnome-terminal"). Again, this must correspond to a folder in the templates directory. Replace SUBTEMPLATE_NAME with the name of the subtemplate as it is defined at the top level of the template's config.yaml file (see `here <https://github.com/chriskempson/base16/blob/master/file.md>_` for details). If you omit the subtemplate name (don't omit ## though), "default" is assumed.

An example of an i3 config file prepared in such a way (and used for testing purposes) can be found `here <https://github.com/InspectorMustache/pybase16-builder/blob/master/tests/test_config>_`.

Provide a path to the colorscheme you wish to inject by pointing to its YAML file with the -s option. Use the -f option for each file into which you want to inject the scheme.

As an example, here's the command I use to globally change the color scheme in all applications that support it::
    pybase16 inject -s schemes/default/ocean.yaml -f ~/.gtkrc-2.0.mine -f ~/.config/dunst/dunstrc -f ~/.config/i3/config -f ~/.config/termite/config -f ~/.config/zathura/zathurarc
