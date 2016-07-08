#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import os
import os.path

def check_type(value, value_type):
    """
    Recursively check the types of the value against the value_type spec

    Only handles native types that could be decoded from a json blob
    """

    if value_type is None:
        return True
    elif isinstance(value_type, ComplexType):
        return check_type(value, value_type.base_type) and value_type.check(value)
    elif isinstance(value_type, dict):
        try:
            return all(check_type(value[k], v) for (k, v) in value_type.iter_items())
        except KeyError:
            return False
    elif isinstance(value_type, (list, tuple)):
        item_type = value_type[0]
        return (item_type is None) or all(check_type(v, item_type) for v in value)
    else:
        if value_type in (int, long):
            value_type = (int, long)
        return isinstance(value, value_type)

class ComplexType(object):
    def __init__(self, base_type, check_value):
        self._base_type = base_type
        self._check_value = check_value

    @property
    def base_type(self):
        return self._base_type

    def check(self, value):
        return True

class RegexMatch(ComplexType):
    def __init__(self, base_type, check_value):
        super(RegexMatch, self).__init__(base_type, re.compile(check_value))

    def check(self, value):
        return bool(self._check_value.search(value))

UUID = RegexMatch(basestring,
    r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}')

class InclusiveRange(ComplexType):
    def check(self, value):
        return (self._check_value[0] <= value) and \
            (value <= self._check_value[1])

def safe_path_join(a, *p):
    return os.path.join(a, *(s.lstrip(os.sep) for s in p))
