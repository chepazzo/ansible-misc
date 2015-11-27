'''
 This is a collection of filters that deals with lists of dicts
'''
from __future__ import absolute_import

from ansible import errors

class FilterModule(object):
    ''' Ansible list-of-dicts jinja2 filters '''

    def filters(self):
        return {
            'pluck': pluck,
            'stitch': stitch,
            'merge': merge,
        }

def pluck(stuff, attr, val):
    '''
    pluck will take a list of dicts and return a subset of dicts
    where the value of the attr field is val.
    ****
        I assume that this is how the 'equalto' test in selectattr() is supposed
        to work in jinja2 v2.8, 
            {{ mounts|selectattr("fstype", "equalto", "nfs") }}
        but I don't have that intalled, so I had to roll my own.
    ****
    e.g.
    ---
    vars:
      all_mounts:
        web:
          name: /var/www
          src: nfs:/web
          fstype: nfs
        git:
          name: /opt/git
          src: nfs:/git
          fstype: nfs
        pics:
          name: /data/pics
          src: nfs:/pics
          fstype: nfs

    tasks:
    - name: mount only NFS shares
      mount: 
        name="{{ item.name }}" 
        src="{{ item.src }}" 
        fstype="{{ item.fstype }}" 
        state="mounted" 
        opts="{{ item.opts }}"
      with_items:
        all_mounts|pluck('fstype','nfs')

    '''
    return [s for s in stuff if s.get(attr) == val]

def stitch(stuff, data, attr=None):
    '''
    Stitch will take a list of labels and map each to a dicts.
    Use the optional attr if the initial list is of dicts.
    e.g.
    ---
    vars:
      ## e.g. put this in group_vars/all
      ## define mount points
      all_mounts:
        web:
          name: /var/www
          src: nfs:/web
          fstype: nfs
        git:
          name: /opt/git
          src: nfs:/git
          fstype: nfs
        pics:
          name: /data/pics
          src: nfs:/pics
          fstype: nfs

      ## e.g. put this in group_vars/webservers
      ## configure which mounts go on which devices
      mounts:
        - web
        - pics

    tasks:
    - name: mount
      mount: 
        name="{{ item.name }}" 
        src="{{ item.src }}" 
        fstype="{{ item.fstype }}" 
        state="mounted" 
        opts="{{ item.opts }}"
      with_items:
        mounts|stitch(all_mounts)

    ---
    vars:
      mounts:
        - name: web
          comment: My web server needs web stuff
        - name: pics
          comment: My web server needs pics

    tasks:
    - name: mount
      mount: 
        name="{{ item.name }}" 
        src="{{ item.src }}" 
        fstype="{{ item.fstype }}" 
        state="mounted" 
        opts="{{ item.opts }}"
      with_items:
        mounts|stitch(all_mounts,'name')

    '''
    if attr is None:
        return [data[s] for s in stuff]
    else:
        ret = []
        for s in stuff:
            newd = {}
            newd.update(data[s[attr]])
            if attr not in newd.keys():
                newd[attr] = s[attr]
            ret.append(newd)
        #return [data[s[attr]] for s in stuff]

def merge(stuff, data, attr, filter=False):
    '''
    Merge two lists of dicts by matching a common attr.
    This is quite useful for abstracting vendor/model-specific 
    values from intent.

    ---
    vars:
      ## Place this in a generic group_vars
      ## e.g. group_vars/leaf
      ## 'interfaces' describes the intent
      ## "leaf switches need uplinks in ospf area 0 and peerlinks in area 100"
      interfaces:
        - label: uplinks
          ospf:
            area: 0.0.0.0
            type: p2p
          mtu: jumbo
        - label: peerlinks
          ospf:
            area: 0.0.0.100
            type: p2p
          mtu: standard
      ## Place this in a generic group_vars
      ## e.g. group_vars/leaf-juniper-ex4200
      ## 'int_defs' defines labels
      ## "On leaf switches, the uplinks are xe-0/1/0 and xe-0/1/2"
      int_defs:
        uplinks:
          - name: xe-0/1/0
            speed: 10G
          - name: xe-0/1/2
            speed: 10G
        peerlinks:
          - name: ge-0/0/0
            speed: 1G
          - name: ge-0/0/1
            speed: 1G

    tasks:
      - name: configure ospf ints
        debug: var=item
        with_items:
          interfaces|merge(int_defs,'label')

    ---
    ## Alternate organization
    vars:
      int_defs:
        - { name: xe-0/1/0, label: uplinks }
        - { name: xe-0/1/2, label: uplinks }
        - { name: ge-0/0/0, label: peerlinks }
        - { name: ge-0/0/1, label: peerlinks }
      interfaces:
        - label: uplinks
          ospf:
            area: 0.0.0.0
            type: p2p
        - label: peerlinks
          ospf:
            area: 0.0.0.100
            type: p2p

    tasks:
      - name: configure ospf ints
        debug: var=item
        with_items:
          interfaces|merge(int_defs,'label')

    ---
    vars:
      ## Place this in a generic group_vars
      ## e.g. group_vars/leaf
      interfaces:
        - label: uplinks
          ospf:
            area: 0.0.0.0
            type: p2p
        - label: peerlinks
          ospf:
            area: 0.0.0.100
            type: p2p
      ## Place this in a generic group_vars
      ## e.g. group_vars/leaf-juniper-ex4200
      int_defs:
        uplinks:
          - name: xe-0/1/0
          - name: xe-0/1/2
        peerlinks:
          - name: ge-0/0/0
          - name: ge-0/0/1
      ## Place this in a host_vars
      ## e.g. host_vars/leaf1-sw.site.net.com
      int_config:
        - name: xe-0/1/0
          ipv4:
            cidr: 1.1.1.1/24
        - name: xe-0/1/2
          ipv4:
            cidr: 2.2.2.2/24

    tasks:
      - name: display merged interfaces
        debug: var=item
        with_items:
          interfaces|merge(int_defs,'label')|merge(int_config,'name')

    '''
    retlist = []
    merged = []
    for s in stuff:
        label = s
        ## If attr is specified, matching label is value of attr field.
        ## otherwise, assume stuff is a list of labels.
        if attr is not None:
            if attr in s:
                label = s[attr]
            else:
                ## If the attr is not in /s/, then it's not going to match
                ## anything in data, so either:
                ## - move on to the next /s/ (if filter)
                ## - or add /s/ to return val and move on to the next /s/.
                if filter:
                    continue
                newd = {}
                newd.update(s)
                retlist.append(newd)
                continue
        ## Find a list of dicts that match the key:val pairing for s.
        ## datalist[] should be a list of dicts (d) where d[attr] == label
        if 'keys' in dir(data):
            ## if data is a dict, assume that the keys are labels and
            ## the values are lists that need to be merged into stuff. 
            datalist = data.get(label,[])
        else:
            ## If data is a list of dicts, then the labels are attributes 
            ## of the dicts. 
            datalist = [ d for d in data if d.get(attr,None) == label ]
        if len(datalist) == 0:
            ## if datalist is empty, there is nothing to merge.
            retlist.append(s)
            continue
        ## Time to merge lists
        ## There might be multiple /d/ matches for each /s/
        merged.append(s)
        for d in datalist:
            newd = {}
            newd.update(s)
            newd.update(d)
            retlist.append(newd)
            merged.append(d)
    if not filter:
        if 'keys' in dir(data):
            for k in data.keys():
                for v in data[k]:
                    if v not in merged:
                        v[attr] = k
                        retlist.append(v)
        else:
            for v in data:
                if v not in merged:
                    retlist.append(v)
    return retlist

