import http.client
import http.cookiejar
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import time
import inspect


class CloudAPI:
    username = ''
    password = ''
    version = '4.8.20'
    baseurl = 'https://sso.ubnt.com/api/sso/v1'
    loggedin = False
    debug = False
    cookies = ''
    requesttype = 'POST'
    site = 'default'

    def log(self, *args):
        if self.debug:
            print(*args)

    def __init__(self, username=None, password=None, debug=None,
                 requesttype=None, baseurl=None):
        if username:
            self.username = username
        if password:
            self.password = password
        if debug:
            self.debug = debug
        if requesttype:
            self.requesttype = requesttype
        if baseurl:
            self.baseurl = baseurl

        ssl._create_default_https_context = ssl._create_unverified_context # This is the way to allow unverified SSL
        self.cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1 if self.debug else 0),
                                             urllib.request.HTTPSHandler(debuglevel=1 if self.debug else 0),
                                             urllib.request.HTTPCookieProcessor(self.cj))
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)

    def request(self, url, data=None, headers=None, method='POST', baseurl = None):
        # req = None
        headers = headers or {
            'Content-type': 'application/json',
            'Referer': 'https://account.ubnt.com/login?redirect=https%3A%2F%2Funifi.ubnt.com',
            'Origin': 'https://account.ubnt.com',
            'dnt': 1
        }
        if not baseurl:
            baseurl = self.baseurl
        self.log('Request to %s with data %s' % (baseurl + url, data))
        if data:
            req = urllib.request.Request(url=baseurl + url, data=json.dumps(data).encode("utf8"), headers=headers, method=method)
        else:
            req = urllib.request.Request(url=baseurl + url, headers=headers, method='GET')
        return urllib.request.urlopen(req)

    def reqjson(self, url, data=None, headers=None, method='POST', autologin=True, baseurl=None):
        if autologin:
            self.login()
        resp = self.request(url, data, headers, method, baseurl)
        content = json.loads(resp.read().decode('utf8'))
        return content

    def response(self, content, type="UnifiError", description="UnifiError"):
        if 'meta' in content and 'rc' in content['meta'] and content['meta']['rc'] == 'ok':
            self.log('%s, %s completed successfully' % (type, description))
            return content
        self.log('%s, %s completed not successfully' % (type, description))
        raise Exception(type, description, content)

    def login(self, username=None, password=None):
        """
        Login the system
        :param username:
        :param password:
        :return:
        """
        if self.loggedin:
            return
        if username:
            self.username = username
        if password:
            self.password = password
        try:
            content = self.reqjson("/login",
                                   {'user': self.username, 'password': self.password},
                                   autologin=False
                                   )
            self.log("Successful logged in to %s with %s" % (self.baseurl, self.username))
            self.log("Response: %s" % content)
            self.log("Cookies: %s" % self.cj)
            self.loggedin = True
            return content
        except urllib.error.HTTPError as e:
            self.log("Cannot log in to %s with %s" % (self.baseurl, self.username))
            self.log("Problem is %s" % e)
            self.loggedin = False
            return {}

    def logout(self):
        """
        Logout
        :return:
        """
        if not self.loggedin:
            return
        resp = self.request("/logout"," ")
        self.log('Resp is %s' % resp.read())
        self.loggedin = False
        return {}

    def self(self):
        """
        Get information about yourself
        :return:
        """
        content = self.reqjson("/user/self")
        return content

    def devices(self):
        """
        List the registered devices
        :return:
        """
        content = self.reqjson("/devices", baseurl="https://device-airos.svc.ubnt.com/api/airos/v1/unifi")
        return content

    def delete_device(self, device_id):
        """
        Delete device by device id
        :param device_id:
        :return:
        """
        content = self.reqjson("/devices/"+str(device_id),
                               baseurl="https://device-airos.svc.ubnt.com/api/airos/v1/unifi",
                               method = "DELETE"
                               )
        return content
