# -*- coding: utf-8 -*-


def parse_float(val):
    if val:
        try:
            return float(val.strip())
        except ValueError:
            val = ''.join(filter(unicode.isdigit or '.', val))
            return float(val if len(val) > 0 else 0)
    return 0


def parse_str(val):
    if val and isinstance(val, basestring):
        return val.strip()
    return ""


def parse_int(val):
    if val:
        try:
            return int(val.strip())
        except ValueError:
            val = ''.join(filter(unicode.isdigit or '.', val))
            return int(val if len(val) > 0 else 0)
    return 0
