#!/usr/bin/env python3
'''
Use for mapping a local web application with known accessible structure
'''
import queue
import threading
import os
import requests
import time

threads = 10

target = 'http://172.28.128.3'  # local Damn Vulnerable Web App VM
directory = 'webmapper'
filters = ['.jpg', '.gif', '.png', '.css']

os.chdir(directory)

web_paths = queue.Queue()

for r, d, f in os.walk('.'):
    for files in f:
        remote_path = '{}/{}'.format(r, files)
        if remote_path.startswith('.'):
            remote_path = remote_path[1:]
        if os.path.splitext(files)[1] not in filter:
            web_paths.put(remote_path)


def test_remote():
    while not web_paths.empty():
        path = web_paths.get()
        url = '{}{}'.format(target, path)
        try:
            response = requests.get(url)
            print('[{}] => {}'.format(response.status_code, path))
        except requests.ConnectionError:
            print('Connection problem.')
            raise
        except Exception:
            print('Problem getting website path: {}'.format(path))
            raise


for i in range(threads):
    print('Thread: {}'.format(i))
    t = threading.Thread(target=test_remote)
    t.start()
    time.sleep(0.5)
