#!/usr/bin/env python3
import os.environ


def run(**args):
    print('[*] In environment module')
    return str(os.environ)
