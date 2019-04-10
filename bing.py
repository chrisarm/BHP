from burp import IBurpExtender
from burp import IContextMenuFactory

from javax.swing import JMenuItem
from java.util import List, ArrayList
from java.net import URL

import socket
import urllib
import json
import re
import base64
import threading
import time
import sys

with open('api_key.txt','r') as api_file:
    bing_api_key = api_file.readline()
    
gverbose = False


def vprint(verbose_string, lverbose=False):
    '''
        Enables verbose printing with a custom line icon in brackets.
    '''
    global gverbose
    if lverbose or gverbose:
        if gverbose is True:
            icon = '[*]'
        else:
            icon = '[{}]'.format(lverbose)
        print('{} {}'.format(icon, verbose_string))
        sys.stdout.flush()


class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None

        callbacks.setExtensionName("Bing IP Search")
        callbacks.registerContextMenuFactory(self)

        return

    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem(
            'Send to Bing',
            actionPerformed=self.bing_menu_event))
        return menu_list

    def bing_menu_event(self, event):
        # Grab details of what the user clicked
        http_traffic = self.context.getSelectedMessages()

        vprint('{} requests highlighted'.format(len(http_traffic)))

        for traffic in http_traffic:
            http_service = traffic.getHttpService()
            host = http_service.getHost()

            vprint('User selected host: {}'.format(host))
            self.bing_search(host)

        return

    def bing_search(self, host):
        is_ip = re.match('[0-9]+(?:\.[0-9]+){3}', host)
        if is_ip:
            ip_address = host
            domain = False
        else:
            ip_address = socket.gethostbyname(host)
            domain = True
            vprint('Found Domain IP: {}'.format(ip_address))
        bing_query_string = 'ip:{}'.format(ip_address)

        try:
            t1 = threading.Thread(target=self.bing_query, args=(bing_query_string,))
            t1.start()

            if domain:
                bing_query_string = 'domain:{}'.format(host)
                t1 = threading.Thread(target=self.bing_query, args=(bing_query_string,))
                t1.start()

            timeout = True
            current_time = time.time()
            while (t1.is_alive) and timeout:
                time.sleep(1)
                if time.time() - current_time > 7:
                    timeout = False
                    vprint('Timed out.')

        except Exception as ebs:
            vprint('Problem while starting Bing search')
            raise

    def bing_query(self, bing_query_string):
        quoted_query = urllib.quote(bing_query_string)
        http_request = 'GET /bing/v7.0/Search?'
        http_request += 'q={query}&count=10 HTTP/1.1\r\n'.format(query=quoted_query)
        http_request += 'Host: api.cognitive.microsoft.com\r\n'
        http_request += 'Connection: close\r\n'
        http_request += 'Ocp-Apim-Subscription-Key: {apikey}\r\n'.format(apikey=bing_api_key)
        http_request += 'User-Agent: BHP\r\n\r\n'
        vprint('Performing Bing search:\r\n{}'.format(http_request))
        try:
            json_body = self._callbacks.makeHttpRequest('api.cognitive.microsoft.com', 443, True, http_request)
            json_string = self._helpers.bytesToString(json_body).split('\r\n\r\n', 1)[1]
            vprint('HTTP request completed. {}'.format(json_string))
        except Exception as eb1:
            vprint('Problem performing Bing search. {}'.format(eb1))
            vprint('\r\n{}'.format(json_string))
            raise
        try:
            r = json.loads(json_string)
            results = r['webPages']['value']
            if results:
                for site in results:
                    print('*' * 100)
                    print(site['name'])
                    print(site['displayUrl'])
                    print(site['snippet'])
                    print('*' * 100)

                    j_url = URL(site['url'])

                    if not self._callbacks.isInScope(j_url):
                        vprint('Adding to Burp scope')
                        self._callbacks.includeInScope(j_url)
            else:
                raise ValueError('No results received from Bing.')
        except Exception as eb:
            vprint(r.keys())
            vprint('HTTP request failed.\r\n{}'.format(json.dumps(r, indent=2)))
            vprint('Unexpected results from Bing. {}'.format(eb))
            raise
        return
