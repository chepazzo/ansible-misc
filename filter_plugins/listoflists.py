'''
 This is a collection of filters that deals with lists of lists
'''
from __future__ import absolute_import

from ansible import errors
import itertools

class FilterModule(object):
    ''' Ansible list-of-dicts jinja2 filters '''

    def filters(self):
        return {
            'collapse': collapse,
            'expand_ranges': expand_ranges,
        }

def collapse(stuff):
    '''
    collapse will take a list of list and return a single list
    This really should perform the same function as with_flatten,
    excpet that you can use it in a jinja2 template.
    '''
    return list(itertools.chain.from_iterable(stuff))

def expand_ranges(stuff):
    '''
    Expands lists with embedded ranges to a single list
    e.g. 
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
          ints|expand_ranges
    '''
    ret = []
    for s in stuff:
        if s['name'] != 'range':
            ret.append(s)
            continue
        for num in range(*s['range']):
            thing = {}
            thing.update(s)
            thing['name'] = "%s%s"%(s['prefix'],num)
            ret.append(thing)
    return ret

