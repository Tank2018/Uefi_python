# -*- coding: utf-8 -*-
import struct

def sguid(b, big=False):
    '''RFC4122 binary GUID as string.'''
    if b is None or len(b) != 16:
        return ""
    a, b, c, d = struct.unpack("%sIHH8s" % (">" if big else "<"), b)
    d = ''.join('%02x' % ord(c) for c in d)
    return "%08x-%04x-%04x-%s-%s" % (a, b, c, d[:4], d[4:])

def dhex(b, big=False):
    '''RFC4122 binary GUID as string.'''
    if b is None or len(b) != 16:
        return ""
    a = struct.unpack("%s16B" % (">" if big else "<"), b)
    d = ''.join('%02x ' % c for c in a)
    return d


def dmpehex(data):
    for i in range(0, 16, 1):
        print dhex(data[:16])
        data = data[16:]
    pass

