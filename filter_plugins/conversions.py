'''
 This is a collection of filters that deal with conversions
'''
from __future__ import absolute_import

from ansible import errors

class FilterModule(object):
    ''' Ansible conversion jinja2 filters '''

    def filters(self):
        return {
            'fmtsize': fmtsize,
        }

def fmtsize(val,targ,case='lower',base=10):
    '''
    fmtsize will take a string representing a size and convert it to or from 
    human-readable format.
    params: 
      targ: human => 100g, 10m, 1k, etc
            raw => 100000000000, 10000000, 1000, etc
            ## Perpaps one day I can add 'float'
      case: 'upper' or 'lower'
      k: is 1k=1000 or 1k=1024
    e.g.
    ---
    vars:
      interfaces:
        - name: eth1
          speed: 1g
        - name: xe-1/0/0
          speed: 10g

    tasks:
    - name: show me interfaces
      debug: msg="{{ item.name }} is a {{ item.speed|fmtsize('human',case='upper') }} interface which is {{ item.speed|fmtsize('raw')/1000000 }} Mbps"
      with_items:
        interfaces
    '''
    # I would prefer to use the correct capitalization, but 
    # dict lookups become much harder when the input might
    # be wrong.
    valid_suffixes = [ '', 'K','M','G','T','P','E','Z','Y' ]
    ## The power multiplier tells us how to get the number
    ## e.g. for K (1), base2 = pow(2,1*10) = 1024;    base10 = pow(10,1*3) = 1000
    ##      for M (2), base2 = pow(2,2*10) = 1048576; base10 = pow(10,2*3) = 1000000
    ## etc
    pow_mult = { 2: 10, 10: 3 }
    kfactor = pow(base,pow_mult[base])
    def _to_human(num):
        if _is_valid_human(num):
            return num
        if type(num) is str:
            if not num.isdigit():
                return None
            num = int(num)
        if type(num) is not int:
            return None
        for x in valid_suffixes:
            if num < kfactor:
                if case == 'lower':
                    x = x.lower()
                return "%s%s" % (num, x)
            num /= kfactor
        return None
    def _to_raw(text):
        if type(text) is int:
            return text
        if text.isdigit():
            return int(text)
        if not _is_valid_human(text):
            return None
        n = int(text[:-1])
        s = text[-1:].upper()
        power = valid_suffixes.index(s)*pow_mult[base]
        raw = n*pow(base,power)
        return raw
    def _is_valid_human(text):
        if type(text) is int:
            n = text
            s = None
        else:
            n = text[:-1]
            if not n.isdigit(): return False
            n = int(n)
            s = text[-1:].lower()
        if s not in [x.lower() for x in valid_suffixes]:
            if n < kfactor:
                return True
            return False
        return True
    if targ =='human': return _to_human(val)
    if targ =='raw': return _to_raw(val)

