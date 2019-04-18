#!/usr/bin/env python3
import os


def run(**args):
    print('[*] In environment module')
    return str(os.environ)
