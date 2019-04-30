#!/usr/bin/env python3
import os


def run(**args, test=False):
    print('[*] In environment module')
    if test:
        return 'Environment variables could be printed'
    else:
        return str(os.environ)
