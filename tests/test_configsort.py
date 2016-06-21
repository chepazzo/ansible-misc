# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import unittest
from library.configsort import sort_config

class SortTestCase(unittest.TestCase):

    def test_basic_sort(self):
        orig_config = """
interface eth 3
  ip address 3.3.3.3/32
  load interval 5
interface eth 1
  ip address 1.1.1.1/32
  description "eth1 rules"
  load interval 5
        """
        exp_config = """
interface eth 1
  description "eth1 rules"
  ip address 1.1.1.1/32
  load interval 5
interface eth 3
  ip address 3.3.3.3/32
  load interval 5
        """.strip()
        sorted_config = sort_config(orig_config.split('\n'))
        self.assertEqual('\n'.join(sorted_config), exp_config, '')

    def test_duplicate_top_level(self):
        orig_config = """
interface eth 3
  load interval 5
interface eth 1
  ip address 1.1.1.1/32
  description "eth1 rules"
  load interval 5
interface eth 3
  ip address 3.3.3.3/32
        """
        exp_config = """
interface eth 1
  description "eth1 rules"
  ip address 1.1.1.1/32
  load interval 5
interface eth 3
  ip address 3.3.3.3/32
  load interval 5
        """.strip()
        sorted_config = sort_config(orig_config.split('\n'))
        self.assertEqual('\n'.join(sorted_config), exp_config, '')

    def test_duplicate_sub_level(self):
        orig_config = """
interface eth 3
  load interval 5
interface eth 1
  ip address 1.1.1.1/32
  description "eth1 rules"
  load interval 5
  description "eth1 rules"
interface eth 3
  load interval 5
  ip address 3.3.3.3/32
        """
        exp_config = """
interface eth 1
  description "eth1 rules"
  ip address 1.1.1.1/32
  load interval 5
interface eth 3
  ip address 3.3.3.3/32
  load interval 5
        """.strip()
        sorted_config = sort_config(orig_config.split('\n'))
        self.assertEqual('\n'.join(sorted_config), exp_config, '')

    def test_multi_level(self):
        orig_config = """
interface eth 1
  ip address 1.1.1.1/32
  description "eth1 rules"
  load interval 5
  ip ospf
    passive
    area 0
interface eth 3
  load interval 5
  ip address 3.3.3.3/32
  ip ospf
    passive
    nssa
    area 100
        """
        exp_config = """
interface eth 1
  description "eth1 rules"
  ip address 1.1.1.1/32
  ip ospf
    area 0
    passive
  load interval 5
interface eth 3
  ip address 3.3.3.3/32
  ip ospf
    area 100
    nssa
    passive
  load interval 5
        """.strip()
        sorted_config = sort_config(orig_config.split('\n'))
        self.assertEqual('\n'.join(sorted_config), exp_config, '')

    def test_multi_level_dup(self):
        orig_config = """
interface eth 3
  description "eth3 forever"
  ip ospf
    passive
    auth-key none
interface eth 1
  ip address 1.1.1.1/32
  description "eth1 rules"
  load interval 5
  ip ospf
    passive
    area 0
interface eth 3
  load interval 5
  ip address 3.3.3.3/32
  ip ospf
    passive
    nssa
    area 100
        """
        exp_config = """
interface eth 1
  description "eth1 rules"
  ip address 1.1.1.1/32
  ip ospf
    area 0
    passive
  load interval 5
interface eth 3
  description "eth3 forever"
  ip address 3.3.3.3/32
  ip ospf
    area 100
    auth-key none
    nssa
    passive
  load interval 5
        """.strip()
        sorted_config = sort_config(orig_config.split('\n'))
        self.assertEqual('\n'.join(sorted_config), exp_config, '')

if __name__ == '__main__':
    unittest.main()

