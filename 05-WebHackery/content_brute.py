#!/usr/bin/env python3
'''
Use for investigating web application structure from public facing access
'''
import requests
import threading
import queue

threads = 5
target_url = 'http://172.28.128.3'

wordlist_file = '/usr/share/wordlists/dirb/big.txt'
resume = None
user_agent = (
    'Mozilla/5.0 (X11; Linux x86_64; '
    'rev:19.0) Gecko/20100101 Firefox/19.0)')


def build_wordlist(wordlist_file):
    with open(wordlist_file, 'rb') as fd:
        raw_words = fd.readlines()

    found_resume = False
    words = queue.Queue()

    for word in raw_words:
        # ignore lines that start with a '#'
        if 35 == word[0]:
            continue
        word = word.rstrip()

        if resume is not None:
            if found_resume:
                words.put(word)
            else:
                if word == resume:
                    found_resume = True
                    print('Resuming from: {}'.format(resume))
        else:
            words.put(word)

    return words


def dir_bruter(word_queue, extensions=None):
    while not word_queue.empty():
        attempt = word_queue.get().decode()
        attempt_list = []

        if '.' not in attempt:
            attempt_list.append('/{}/'.format(attempt))
        else:
            attempt_list.append('/{}'.format(attempt))

        if extensions:
            for extension in extensions:
                attempt_list.append('/{}{}'.format(attempt, extension))

        for brute in attempt_list:
            url = '{}{}'.format(
                target_url,
                requests.utils.requote_uri(brute))
            try:
                headers = {}
                headers['User_Agent'] = user_agent
                response = requests.get(url, headers=headers)
                if response:
                    print('[{}] => {}'.format(response.status_code, url))
            except requests.RequestException as rre:
                if hasattr(rre, 'code') and rre.code != 404:
                    print('!!! {} => {}'.format(rre.code, url))

                pass


word_queue = build_wordlist(wordlist_file)
extensions = ['.php', '.bak', '.orig', '.inc']

for i in range(threads):
    t = threading.Thread(target=dir_bruter, args=(word_queue, extensions,))
    t.start()
