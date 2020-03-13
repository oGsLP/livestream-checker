#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: lenovo by XYF
@file: main.py
@time: 2020/03/12
@function: 
"""

from lib.checker import Checker


def start():
    c = Checker()
    c.read_yml('.list.yml')
    c.add_to_list("斗鱼", 101)
    c.add_to_list("斗鱼", 100)
    c.check()


if __name__ == '__main__':
    start()
