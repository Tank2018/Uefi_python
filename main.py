#!/usr/bin/env python
import os
import sys
import uuid
import copy
import argparse

from firmware import *


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='commands')
    parser_genhdr = subparsers.add_parser('prase',  help='prase uefi bios fv')
    parser_genhdr.set_defaults(which='prase')
    parser_genhdr.add_argument('-f', dest='bin', type=str, help='BIOS binary file path', required = True)

    args = parser.parse_args()
    if args.which == 'prase':
        bios = Firmware (args.bin)
        bios.process()
    print 'Done!'
    return 0


if __name__ == '__main__':
    main()