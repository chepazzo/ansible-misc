#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The config_sort module sorts a configuration file
while maintaining hierarchy. This allows one to perform
a diff between files from different generators.

Args:
    src (str): The source file to sort.
        This is usually the result of an assemble command
    dest (str): The destination file to write sorted config.

Example:
    Playbook Example::

        ---
        tasks:
          - name: compile configuration
            assemble:
              src={{ config_dir }}/{{ inventory_hostname }}
              dest={{ config_dir }}/{{ inventory_hostname }}.config
              regexp="\.fragment$"
          - name: sort config
            config_sort:
              src="configs/{{ inventory_hostname }}.conf"
              dest="configs/{{ inventory_hostname }}.sorted.conf"

Note:
    While this module technically supports check mode, most likely,
    if no other changes were actually made to the file being sorted,
    then this is not going to report any changes.

    i.e. If the generated (unsorted) config file is the same other than the ordering,
    then the task that generated that file will display change, while the task
    that calls this module will report as unchanged.

    This can be used to verify if, after moving or re-organizing roles and tasks,
    the final result is effectively unchanged.

"""

from __future__ import print_function, absolute_import

DOCUMENTATION = """
---
module: config_sort
short_description: Sorts a configuration file.
description:
  - The config_sort module sorts a configuration file 
    while maintaining hierarchy. This allows one to perform
    a diff between files from different generators.
version_added: 1.9
category: System
author: Mike Biancaniello (@chepazzo)
requirements: []
options:
  src:
    description:
      - Specify the source file to sort.
        This is usually the result of an assemble command
    required: true
    version_added: 1.9
  dest:
    description:
      - Specify the dest file to write sorted config.
    required: true
    version_added: 1.9
"""

EXAMPLES = """

tasks:
  - name: sort config
    config_sort:
      src="configs/{{ inventory_hostname }}.conf"
      dest="configs/{{ inventory_hostname }}.sorted.conf"

"""

import os

## NO requirements
REQ_AVAILABLE = True


# try:
#    from requirement import requirement
#    REQ_AVAILABLE = True
# except ImportError:
#    REQ_AVAILABLE = False

class Lineobj(object):
    """A class to hold meta and relative position data about each line in the config.

    Args:
        line (str): The config line to be stored.
        **kwargs: Aribtrary kwargs. This is not currently used.

    Attributes:
        text (str): The text of the configuration line.
        parent (Lineobj): Parent Lineobj. This Lineobj is a ``sub`` of the parent.
        subs (list): List of Lineobjs for which this is the parent line.
        indent (int): Number of spaces this line is indented.

            | This attribute is used to keep track of the hierarchy level.
            | If indent == 0, then there should be no parent.
            | if indent > 0, then this Lineobj should be a sub of another.
    """

    def __init__(self, line, **kwargs):
        self.text = line
        self.parent = None
        self.subs = []
        self.indent = len(line) - len(line.lstrip(' '))
        super(Lineobj, self).__init__()

    def add_sub(self, lineobj):
        """Add sub line in hierarchy.

        If line already exists, then don't add it.

        Args:
          lineobj (Lineobj): An object of this same type to be added as a sub
            line to self.
        """
        for sub in self.subs:
            if sub.text == lineobj.text: return sub
        self.subs.append(lineobj)
        return lineobj


def sort_config(config):
    """This is the top-level function of the module.

    This function can be used outside of Ansible.

    Args:
        config (list): A list of configuration lines.

            | This is usually the result of fh.readlines().

    Returns:
        list: A list of configuration lines, properly sorted.

            | This can be used directly by fh.writelines().
    """
    lines = {}
    currlevel = []
    for line in config:
        if line.strip() == '':
            continue
        lineobj = lines.get(line, Lineobj(line))
        if line.startswith(' '):
            insert_sub(currlevel, lineobj)
            continue
        else:
            currlevel = [lineobj]
            lines[line] = lineobj
            continue
    return get_config(lines.values())

def insert_sub(currlevel, lineobj):
    """Figures out the correct Lineobj to insert the current line
    and resets the currlevel appropriately.

    Args:
        currlevel (list): List of Lineobjs representing the current
            hierarchical level.
        lineobj (Lineobj): Lineobj that needs to be placed.

    Returns:
        None: Returns nothing, but changes the vars passed.
    """
    levellen = len(currlevel)
    # print "currlevel:",currlevel
    for i in range(levellen - 1, -1, -1):
        # print "i",i
        # print "currlevel[{}] = {}".format(i,currlevel[i].text)
        if lineobj.indent <= currlevel[i].indent:
            currlevel.pop()
        else:
            lineobj = currlevel[i].add_sub(lineobj)
            currlevel.append(lineobj)
            break


def get_config(lines):
    """Recursive function that iterates over the hierarchical Lineobjs
    to produce a flat list of config lines.

    Args:
        lines (list): A list of Lineobjs.

            | The Lineobjs in this list are expected to have subs[] set
              to properly represent the config hierarchy.

    Returns:
        list: A *flat* sorted list of config lines that can be used with fh.writelines()
            to write to a configuration file.
    """
    config = []
    for line in sorted(lines, key=lambda k: k.text):
        config.append(line.text)
        config.extend(get_config(line.subs))
    return config


def module_main(module):
    """Main Ansible module function.

    This just does Ansible stuff like collect/format args and set
    value of changed attribute.

    Args:
        module (ansible.module_utils.basic.AnsibleModule): The base ansible module.
    """
    srcfile = module.params['src']
    destfile = module.params['dest']
    with open(srcfile) as _:
        config = _.readlines()
        sorted_config = sort_config(config)
    if os.path.isfile(destfile):
        with open(destfile) as _:
            old_sorted_config = _.readlines()
    else:
        old_sorted_config = []
    result = {}
    diff = {
        'before_header': destfile,
        'before': ''.join(old_sorted_config),
        'after_header': 'dynamically generated',
        'after': ''.join(sorted_config),
    }
    if ''.join(sorted_config) == ''.join(old_sorted_config):
        ## If no changes, return changed=False
        result['changed'] = False
    elif module.check_mode:
        ## If changes, return changed=True, but DO NOT change
        result['changed'] = True
        result['diff'] = diff
    else:
        ## If changes, make changes, return changed=True
        with open(destfile, 'w') as _:
            _.writelines(sorted_config)
        result['changed'] = True
        result['diff'] = diff
    module.exit_json(**result)


def main():
    """Main function for python module.
    """
    argument_spec = dict(
        src=dict(required=True),
        dest=dict(required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if not REQ_AVAILABLE:
        module.fail_json(msg='REQ is required for this module. Install from pip: pip install REQ.')
    module_main(module)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

