'''
 This is a collection of filters that deals with lists of lists
'''
from __future__ import absolute_import

from ansible import errors
import itertools

class FilterModule(object):
    ''' Class to make filters available to Ansible '''

    def filters(self):
        ''' List of filters to import into Ansible '''

        return {
            'collapse': collapse,
            'collapse_dict': collapse_dict,
            'expand_ranges': expand_ranges,
        }

def collapse(stuff):
    '''
    collapse will take a list of list and return a single list
    This is similar to using with_flattened, except that this module
    can be used inside of a jinja2 template.

    Args:
        stuff (list): List of lists that you need to collapse. Usually, this passed via pipe.

    Returns:
        list: A combined flattened list.
    '''
    return list(itertools.chain.from_iterable(stuff))

def collapse_dict(stuff):
    '''
    collapse will take a dict of lists and return a single list
    This is similar to using with_flattened, except that this module
    can be used inside of a jinja2 template.

    Args:
        stuff (dict): Dict of lists that you need to collapse. Usually, this passed via pipe.

    Returns:
        list: A combined flattened list.

    Example:
      vars:
        users:
          apps:
          - name: www-data
            id: 33
          people:
          - name: mike
            id: 1001
          - name: bob
            id: 1002
      tasks:
      - name: show me stuff
        debug: {{users|collapse_dict}}
        

    returns: [{'name': 'www-data', 'id': 33}, {'name': 'mike', 'id': 1001}, {'name': 'bob', 'id': 1002}]
    '''
    return list(itertools.chain.from_iterable(stuff.values()))

def expand_ranges(stuff,field='name'):
    '''
    Expands lists with embedded ranges to a single list.

    Args:
        stuff (list): List of dicts with ranges. Usually, this passed via pipe.
        field (Optional[str]): Name of field that is expected to have a value of 'range'
            for items that need to be expanded.

            This is also the field that will be populated with the output of the expanded range.

    Returns:
        list: Unified list with ranges expanded to multiple items.

    Example:
        Playbook Example::

            ---
            vars:
              ints: 
                - name: range
                  prefix: "ge-0/1/"
                  range: [0,4] 
                - name: ge-1/0/0
                - name: ge-2/0/0
  
            tasks:
              - name: expand_ranges
                debug: var={{ item.name }}
                with_items:
                  ints|expand_ranges('name')
    '''
    ret = []
    for s in stuff:
        if field not in s:
            ret.append(s)
            continue
        if s[field] != 'range':
            ret.append(s)
            continue
        prefix = s.get('prefix','')
        suffix = s.get('suffix','')
        for num in range(*s['range']):
            thing = {}
            thing.update(s)
            thing[field] = "%s%s%s"%(prefix,num,suffix)
            ret.append(thing)
    return ret

