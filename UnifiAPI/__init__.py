import http.client
import http.cookiejar
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import time


class UnifiAPI:
    username = ''
    password = ''
    version = '4.8.20'
    baseurl = 'https://127.0.0.1:8443'
    loggedin = False
    debug = False
    cookies = ''
    requesttype = 'POST'
    site = 'default'

    def log(self, *args):
        if self.debug:
            print(*args)

    def __init__(self, username=None, password=None, version=None, debug=None,
                 requesttype=None, baseurl=None, site=None):
        if username:
            self.username = username
        if password:
            self.password = password
        if version:
            self.version = version
        if debug:
            self.debug = debug
        if requesttype:
            self.requesttype = requesttype
        if baseurl:
            self.baseurl = baseurl
        if site:
            self.site = site

        ssl._create_default_https_context = ssl._create_unverified_context # This is the way to allow unverified SSL
        self.cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1 if self.debug else 0),
                                             urllib.request.HTTPSHandler(debuglevel=1 if self.debug else 0),
                                             urllib.request.HTTPCookieProcessor(self.cj))
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)

    def request(self, url, data=None, headers=None):
        # req = None
        headers = headers or {'Content-type': 'application/json', 'Referer': '/login'}
        self.log('Request to %s with data %s' % (self.baseurl + url, data))
        if data:
            req = urllib.request.Request(url=self.baseurl + url, data=json.dumps(data).encode("utf8"), headers=headers)
        else:
            req = urllib.request.Request(url=self.baseurl + url, headers=headers)
        return urllib.request.urlopen(req)

    def reqjson(self, url, data=None, headers=None):
        self.login()
        resp = self.request(url, data, headers)
        content = json.loads(resp.read().decode('utf8'))
        return content

    def sitecmd(self, url, data=None, headers=None):
        self.login()
        return self.request('/api/s/' + self.site + url, data, headers)

    def sitecmdjson(self, url, data=None, header=None):
        resp = self.sitecmd(url, data, header)
        content = json.loads(resp.read().decode('utf8'))
        return content

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
            resp = self.request("/api/login", {'username': self.username, 'password': self.password})
            content = resp.read()
            self.log("Successful logged in to %s with %s" % (self.baseurl, self.username))
            self.log("Response: %s" % content)
            self.log("Cookies: %s" % self.cj)
            self.loggedin = True
            return json.loads(content.decode('utf8'))
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
        resp = self.request("/logout")
        self.log('Resp is %s' % resp.read())
        self.loggedin = False
        return {}

    def authorize_guest(self, mac, minutes=60, up=None, down=None, mbytes=None, apmac=None):
        """
        Authorize one guest
        :param mac: the mac of the guest
        :param minutes: for how many minutes it is authorized
        :param up: upstream bandwidth in kbits
        :param down: downstream bandwidth in kbits
        :param mbytes: mbytes limit in kbits
        :param apmac: AP mac address (faster performance)
        :return:
        """
        data = {
            'mac': mac.lower(),
            'cmd': 'authorize-guest',
            'minutes': minutes
        }
        if up:
            data['up'] = up
        if down:
            data['down'] = down
        if mbytes:
            data['bytes'] = mbytes
        if apmac:
            data['ap_mac'] = apmac.lower()

        content = self.sitecmdjson('/cmd/stamgr', data)
        if content['meta']['rc'] == 'ok':
            self.log('Authorizing %s was successful' % mac)
            return True
        self.log('Authorizing %s was not successful' % mac)
        return False

    def unauthorize_guest(self, mac):
        """
        Unauthorize one guest
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/stamgr', {
            'cmd': 'unauthorize-guest',
            'mac': mac.lower()
        })
        if content['meta']['rc'] == 'ok':
            self.log('Authorizing %s was successful' % mac)
            return True
        self.log('Authorizing %s was not successful' % mac)
        return False

    def kick_sta(self, mac):
        """
        Reconnect client device
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/stamgr', {
            'cmd': 'kick-sta',
            'mac': mac.lower()
        })
        if content['meta']['rc'] == 'ok':
            self.log('Kicking %s was successful' % mac)
            return True
        self.log('Kicking %s was not successful' % mac)
        return False

    def block_sta(self, mac):
        """
        Blocking client device
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/stamgr', {
            'cmd': 'block-sta',
            'mac': mac.lower()
        })
        if content['meta']['rc'] == 'ok':
            self.log('Blocking %s was successful' % mac)
            return True
        self.log('Blocking %s was not successful' % mac)
        return False

    def unblock_sta(self, mac):
        """
        Unblocking client device
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/stamgr', {
            'cmd': 'unblock-sta',
            'mac': mac.lower()
        })
        if content['meta']['rc'] == 'ok':
            self.log('Unblocking %s was successful' % mac)
            return True
        self.log('Unblocking %s was not successful' % mac)
        return False

    def set_sta_note(self, user, note=''):
        """
        Setting the note of a user device. If the note is empty or not set, note is removed and noted is set to False
        :param user:
        :param note:
        :return:
        """
        content = self.sitecmdjson('/upd/user/' + user, {
            'note': note,
            'noted': True if note else False
        })
        if content['meta']['rc'] == 'ok':
            self.log('Noting %s was successful' % user)
            return True
        self.log('Noting %s was not successful' % user)
        return False

    def set_sta_name(self, user, name=''):
        """
        Setting station name
        :param user:
        :param name:
        :return:
        """
        content = self.sitecmdjson('/upd/user/' + user, {
            'name': name
        })
        if content['meta']['rc'] == 'ok':
            self.log('Naming %s was successful' % user)
            return True
        self.log('Naming %s was not successful' % user)
        return False

    def stat_daily_site(self, start=None, end=None):
        """
        Extracting statistics per site from start to end (unixtimestamps)
        :param start:
        :param end:
        :return:
        """
        unixend = int(time.time()) if end is None else end
        unixstart = (unixend - 52 * 7 * 24 * 3600) if start is None else start
        content = self.sitecmdjson('/stat/report/daily.site', {
            'attrs': ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta', 'lan-num_sta', 'wlan-num_sta',
                      'time'],
            'start': unixstart,
            'end': unixend
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_hourly_site(self, start=None, end=None):
        """
        Extracting statistics per site from start to end (unixtimestamps)
        :param start:
        :param end:
        :return:
        """
        unixend = int(time.time()) if end is None else end
        unixstart = (unixend - 7 * 24 * 3600) if start is None else start
        content = self.sitecmdjson('/stat/report/hourly.site', {
            'attrs': ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta', 'lan-num_sta', 'wlan-num_sta',
                      'time'],
            'start': unixstart,
            'end': unixend
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_hourly_ap(self, start=None, end=None):
        """
        Extracting statistics per site from start to end (unixtimestamps)
        :param start:
        :param end:
        :return:
        """
        unixend = int(time.time()) if end is None else end
        unixstart = (unixend - 7 * 24 * 3600) if start is None else start

        content = self.sitecmdjson('/stat/report/hourly.ap', {
            'attrs': ['bytes', 'num_sta', 'time'],
            'start': unixstart,
            'end': unixend
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_sessions(self, start=None, end=None):
        """
        Extracting sessions
        :param start:
        :param end:
        :return:
        """
        unixend = int(time.time()) if end is None else end
        unixstart = (unixend - 7 * 24 * 3600) if start is None else start
        content = self.sitecmdjson('/stat/session', {
            'type': 'all',
            'start': unixstart,
            'end': unixend
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_sta_sessions_latest(self, mac, limit=None, sort='-assoc_time'):
        """
        Extracting statistics per site from start to end (unixtimestamps)
        :param mac:
        :param limit:
        :param sort:
        :return:
        """
        content = self.sitecmdjson('/stat/session', {
            'mac': mac.lower(),
            '_limit': limit or 5,
            '_sort': sort
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_auths(self, start=None, end=None):
        """
        Return array of authorizations
        :param start:
        :param end:
        :return:
        """
        unixend = int(time.time()) if end is None else end
        unixstart = (unixend - 7 * 24 * 3600) if start is None else start
        content = self.sitecmdjson('/stat/authorization', {
            start: unixstart,
            end: unixend
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_allusers(self, historyhours=8760):
        """
        Return list of client device objects
        :param historyhours:
        :return:
        """
        content = self.sitecmdjson('/stat/alluser', {
            'type': 'all',
            'conn': 'all',
            'within': historyhours
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_guests(self, historyhours=8760):
        """
        Return list of valid access client objects
        :param historyhours:
        :return:
        """
        content = self.sitecmdjson('/stat/guest', {
            'within': historyhours
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_clients(self, mac=None):
        """
        List online clients or client
        :param mac:
        :return:
        """
        # TODO: Fix this one, as it is not working
        content = self.sitecmdjson('/stat/sta/' + (urllib.parse.quote(mac) if mac else ''))
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_client(self, mac=None):
        """
        Single device statistics
        :param mac:
        :return:
        """
        # TODO: Fix this one as it is not working
        content = self.sitecmdjson('/stat/user/' + (urllib.parse.quote(mac) if mac else ''))
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_usergroup(self):
        """
        Respond with the user group
        :return:
        """
        content = self.sitecmdjson('/list/usergroup')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def set_usergroup(self, userid, groupid):
        content = self.sitecmdjson('/upd/user/' + userid, {
            'usergroup_id': groupid
        })
        if content['meta']['rc'] == 'ok':
            self.log('Set user %s group %s was successful' % (userid, groupid))
            return True
        self.log('Set user %s group %s was not successful' % (userid, groupid))
        return False

    def list_health(self):
        """
        Health metric objects
        :return:
        """
        content = self.sitecmdjson('/stat/health')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_dashboard(self):
        """
        List dashboards
        :return:
        """
        content = self.sitecmdjson('/stat/dashboard')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_users(self):
        """
        List users
        :return:
        """
        content = self.sitecmdjson('/list/user')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_aps(self, mac=None):
        """
        List aps
        :return:
        """
        # TODO: It is not working with MAC different than None
        content = self.sitecmdjson('/stat/device/' + (urllib.parse.quote(mac) if mac else ''))
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_rogueaps(self, within=24):
        """
        List rogue aps
        :param within:
        :return:
        """
        content = self.sitecmdjson('/stat/rogueap', {
            'within': within
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def list_sites(self):
        """
        List sites
        :return:
        """
        content = self.reqjson('/api/self/sites')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def stat_sites(self):
        """
        Stat sites
        :return:
        """
        content = self.reqjson('/api/stat/sites')
        if content['meta']['rc'] == 'ok':
            self.log('Stat retrieving %s was successful' % self.site)
            return content
        self.log('Stat retrieving %s was not successful' % self.site)
        return content

    def add_site(self, name=None, description=None):
        """
        Add a site
        :param description:
        :param name:
        :return:
        """
        content = self.sitecmdjson('/cmd/sitemgr', {
            'cmd': 'add-site',
            'name': name,
            'desc': description
        })
        if content['meta']['rc'] == 'ok':
            self.log('Adding site %s was successful' % description)
            return content
        self.log('Adding site %s was not successful' % description)
        return content

    def remove_site(self, name, description=None):
        """
        Remove a site
        :param description:
        :param name:
        :return:
        """
        # TODO: Test it
        content = self.sitecmdjson('/cmd/sitemgr', {
            'cmd': 'remove-site',
            'name': name,
            'desc': description
        })
        if content['meta']['rc'] == 'ok':
            self.log('Adding site %s was successful' % description)
            return content
        self.log('Adding site %s was not successful' % description)
        return content

    def list_wlan_groups(self):
        """
        List wlan groups
        :return:
        """
        content = self.sitecmdjson('/list/wlangroup')
        if content['meta']['rc'] == 'ok':
            self.log('List wlan groups for site %s was successful' % self.site)
            return content
        self.log('List wlan groups for site %s was not successful' % self.site)
        return content

    def stat_sysinfo(self):
        """
        Stat sysinfo
        :return:
        """
        content = self.sitecmdjson('/stat/sysinfo')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_self(self):
        """
        List self
        :return:
        """
        content = self.sitecmdjson('/self')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_networkconf(self):
        """
        List self
        :return:
        """
        content = self.sitecmdjson('/list/networkconf')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def stat_voucher(self, createtime=None):
        """
        List vouchers
        :param createtime:
        :return:
        """
        content = self.sitecmdjson('/stat/voucher', {
            'create_time': createtime
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def stat_payment(self, within=None):
        """
        List vouchers
        :param within:
        :return:
        """
        content = self.sitecmdjson('/stat/voucher', {
            'within': within
        })
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def create_hotspot(self, name, password, note=None):
        """
        Create a hotspot
        :param name:
        :param password:
        :param note:
        :return:
        """
        content = self.sitecmdjson('/rest/hotspotop', {
            'note': note,
            'name': name,
            'x_password': password
        })
        if content['meta']['rc'] == 'ok':
            self.log('Add hotspot to site %s was successful' % self.site)
            return True
        self.log('Add hotspot to site %s was not successful' % self.site)
        return False

    def list_hotspot(self):
        """
        List hotspots
        :return:
        """
        content = self.sitecmdjson('/list/hotspotop')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def create_voucher(self, minutes, count=1, quota=0, note=None, up=None, down=None, mbytes=None):
        """
        Adding some vouchers
        :param minutes:
        :param count:
        :param quota:
        :param note:
        :param up:
        :param down:
        :param mbytes:
        :return:
        """
        content = self.sitecmdjson('/cmd/hotspot', {
            'note': note,
            'up': up,
            'down': down,
            'bytes': mbytes,
            'cmd': 'create-voucher',
            'expire': minutes,
            'n': count,
            'quota': quota
        })
        if content['meta']['rc'] == 'ok':
            self.log('Add voucher to site %s was successful' % self.site)
            return True
        self.log('Add voucher to site %s was not successful' % self.site)
        return False

    def revoke_voucher(self, voucher_id):
        """
        Revoking a voucher
        :param voucher_id:
        :return:
        """
        content = self.sitecmdjson('/cmd/hotspot', {
            'cmd': 'delete-voucher',
            '_id': voucher_id
        })
        if content['meta']['rc'] == 'ok':
            self.log('Remove voucher from site %s was successful' % self.site)
            return True
        self.log('Remove voucher from site %s was not successful' % self.site)
        return False

    def list_portforwarding(self):
        """
        List portforwarding
        :return:
        """
        content = self.sitecmdjson('/list/portforward')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_dynamicdns(self):
        """
        List Dynamic DNS
        :return:
        """
        content = self.sitecmdjson('/list/dynamicdns')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_portconf(self):
        """
        List Port Conf
        :return:
        """
        content = self.sitecmdjson('/list/portconf')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_extension(self):
        """
        List Extension
        :return:
        """
        content = self.sitecmdjson('/list/extension')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def list_settings(self):
        """
        List Settings
        :return:
        """
        # TODO: Set settings to be implemented
        content = self.sitecmdjson('/get/setting')
        if content['meta']['rc'] == 'ok':
            self.log('Stats for site %s was successful' % self.site)
            return content
        self.log('Stats for site %s was not successful' % self.site)
        return content

    def restart_ap(self, mac):
        """
        Restart AP
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/devmgr', {
            'cmd': 'restart',
            'mac': mac.lower()
        })
        if content['meta']['rc'] == 'ok':
            self.log('Restart AP to site %s was successful' % self.site)
            return True
        self.log('Restart AP to site %s was not successful' % self.site)
        return False

    def disable_ap(self, ap_id, disable=True):
        """
        Disable AP
        :param ap_id: id of the AP
        :param disable:
        :return:
        """
        # TODO: Test it
        content = self.sitecmdjson('/rest/device/' + urllib.parse.quote(ap_id), {
            'disabled': disable
        })
        if content['meta']['rc'] == 'ok':
            self.log('Disable AP to site %s was successful' % self.site)
            return True
        self.log('Disable AP to site %s was not successful' % self.site)
        return False

    def enable_ap(self, ap_id, disable=False):
        return self.disable_ap(ap_id, disable)

    def set_locate_ap(self, mac):
        """
        Locate AP (flashing)
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/devmgr', {
            'mac': mac.lower(),
            'cmd': 'set-locate'
        })
        if content['meta']['rc'] == 'ok':
            self.log('Locate AP to site %s was successful' % self.site)
            return True
        self.log('Locate AP to site %s was not successful' % self.site)
        return False

    def unset_locate_ap(self, mac):
        """
        Locate AP (disable flashing)
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/devmgr', {
            'mac': mac.lower(),
            'cmd': 'unset-locate'
        })
        if content['meta']['rc'] == 'ok':
            self.log('Locate unset AP to site %s was successful' % self.site)
            return True
        self.log('Locate unset AP to site %s was not successful' % self.site)
        return False

    def site_ledson(self):
        """
        All AP Leds on
        :return:
        """
        content = self.sitecmdjson('/set/setting/mgmt', {
            'led_enabled': True
        })
        if content['meta']['rc'] == 'ok':
            self.log('On Led of AP to site %s was successful' % self.site)
            return True
        self.log('On Led of AP to site %s was not successful' % self.site)
        return False

    def site_ledsoff(self):
        """
        All AP Leds off
        :return:
        """
        content = self.sitecmdjson('/set/setting/mgmt', {
            'led_enabled': False
        })
        if content['meta']['rc'] == 'ok':
            self.log('Off Led of AP to site %s was successful' % self.site)
            return True
        self.log('Off Led of AP to site %s was not successful' % self.site)
        return False

    def set_ap_radiosettings(self, ap_id, radio='ng', channel=1, ht='20', tx_power_mode=0, tx_power=0):
        """
        Set AP settings
        :param ap_id:
        :param radio:
        :param channel:
        :param ht:
        :param tx_power_mode:
        :param tx_power:
        :return:
        """
        content = self.sitecmdjson('/upd/device/' + urllib.parse.quote(ap_id), {
            'radio': radio,
            'channel': channel,
            'ht': ht,
            'tx_power_mode': tx_power_mode,
            'tx_power': tx_power
        })
        if content['meta']['rc'] == 'ok':
            self.log('AP settings to site %s was successful' % self.site)
            return True
        self.log('AP settings to site %s was not successful' % self.site)
        return False

    def set_guestlogin_settings(self, portal_enabled, portal_customized,
                                redirect_enabled, redirect_url, x_password, expire_number, expire_unit, site_id):
        """
        Set settings for guest login
        :param portal_enabled:
        :param portal_customized:
        :param redirect_enabled:
        :param redirect_url:
        :param x_password:
        :param expire_number:
        :param expire_unit:
        :param site_id:
        :return:
        """
        content = self.sitecmdjson('/set/setting/guest_access', {
            'portal_enabled': portal_enabled,
            'portal_customized': portal_customized,
            'redirect_enabled': redirect_enabled,
            'redirect_url': redirect_url,
            'x_password': x_password,
            'expire_number': expire_number,
            'expire_unit': expire_unit,
            'site_id': site_id
        })
        # TODO: Test it
        if content['meta']['rc'] == 'ok':
            self.log('Guest portal settings to site %s was successful' % self.site)
            return True
        self.log('Guest portal settings to site %s was not successful' % self.site)
        return False

    def rename_ap(self, ap_id, ap_name):
        """
        Rename one AP to another name
        :param ap_id:
        :param ap_name:
        :return:
        """
        # TODO: test
        content = self.sitecmdjson('/upd/device/' + str(ap_id), {
            'name': ap_name
        })
        if content['meta']['rc'] == 'ok':
            self.log('Rename AP for site %s was successful' % self.site)
            return True
        self.log('Rename AP for site %s was not successful' % self.site)
        return False

    def set_wlansettings(self, wlan_id, x_password, name=None):
        """
        Set wlan settings
        :param wlan_id:
        :param x_password:
        :param name:
        :return:
        """
        # TODO: test
        content = self.sitecmdjson('/upd/wlanconf/' + str(wlan_id), {
            'x_passphrase': x_password,
            'name': name
        })
        if content['meta']['rc'] == 'ok':
            self.log('Wlan settings to site %s was successful' % self.site)
            return True
        self.log('Wlan settings to site %s was not successful' % self.site)
        return False

    def list_events(self):
        """
        List the events
        :return:
        """
        content = self.sitecmdjson('/stat/event')
        if content['meta']['rc'] == 'ok':
            self.log('List events to site %s was successful' % self.site)
            return content
        self.log('List events to site %s was not successful' % self.site)
        return content

    def list_wlanconf(self):
        """
        List wlan config
        :return:
        """
        content = self.sitecmdjson('/list/wlanconf')
        if content['meta']['rc'] == 'ok':
            self.log('Wlan settings from site %s was successful' % self.site)
            return content
        self.log('Wlan settings from site %s was not successful' % self.site)
        return content

    def list_alarms(self):
        """
        List the alarms
        :return:
        """
        content = self.sitecmdjson('/list/alarm')
        if content['meta']['rc'] == 'ok':
            self.log('List alarms to site %s was successful' % self.site)
            return content
        self.log('List alarms to site %s was not successful' % self.site)
        return content