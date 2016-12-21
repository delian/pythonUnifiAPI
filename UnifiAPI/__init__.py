import http.client
import http.cookiejar
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import time
import inspect


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

    def request(self, url, data=None, headers=None, method='POST'):
        # req = None
        headers = headers or {'Content-type': 'application/json', 'Referer': '/login'}
        self.log('Request to %s with data %s' % (self.baseurl + url, data))
        if data:
            req = urllib.request.Request(url=self.baseurl + url, data=json.dumps(data).encode("utf8"), headers=headers, method=method)
        else:
            req = urllib.request.Request(url=self.baseurl + url, headers=headers, method='GET')
        return urllib.request.urlopen(req)

    def reqjson(self, url, data=None, headers=None, method='POST'):
        self.login()
        resp = self.request(url, data, headers, method)
        content = json.loads(resp.read().decode('utf8'))
        return content

    def sitecmd(self, url, data=None, headers=None, method='POST'):
        self.login()
        return self.request('/api/s/' + self.site + url, data, headers, method)

    def sitecmdjson(self, url, data=None, header=None, method='POST'):
        resp = self.sitecmd(url, data, header, method)
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
        return self.response(content, inspect.stack()[0].function, 'Guest Authorization')

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
        return self.response(content, inspect.stack()[0].function, 'Guest Unuthorization')

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
        return self.response(content, inspect.stack()[0].function, 'Kicking Station')

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
        return self.response(content, inspect.stack()[0].function, 'Blocking Station')

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
        return self.response(content, inspect.stack()[0].function, 'Unblocking Station')

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
        return self.response(content, inspect.stack()[0].function, 'Set Station Note')

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
        return self.response(content, inspect.stack()[0].function, 'Setting Station Name')

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
        return self.response(content, inspect.stack()[0].function, 'Daily Statistics for site')

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
        return self.response(content, 'Stat_hourly', 'Hourly Statistics for site')

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
        return self.response(content, inspect.stack()[0].function, 'Hourly Statistics for AP')

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
        return self.response(content, inspect.stack()[0].function, 'Session Statistics')

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
        return self.response(content, inspect.stack()[0].function, 'Station session statistics')

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
        return self.response(content, inspect.stack()[0].function, 'Authentication Statistics')

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
        return self.response(content, inspect.stack()[0].function, 'All users statistics')

    def list_guests(self, historyhours=8760):
        """
        Return list of valid access client objects
        :param historyhours:
        :return:
        """
        content = self.sitecmdjson('/stat/guest', {
            'within': historyhours
        })
        return self.response(content, inspect.stack()[0].function, 'List guests')

    def list_clients(self, mac=None):
        """
        List online clients or client
        :param mac:
        :return:
        """
        # TODO: Fix this one, as it is not working
        content = self.sitecmdjson('/stat/sta/' + (urllib.parse.quote(mac) if mac else ''))
        return self.response(content, inspect.stack()[0].function, 'List clients')

    def stat_client(self, mac=None):
        """
        Single device statistics
        :param mac:
        :return:
        """
        # TODO: Fix this one as it is not working
        content = self.sitecmdjson('/stat/user/' + (urllib.parse.quote(mac) if mac else ''))
        return self.response(content, inspect.stack()[0].function, 'Single device statistics')

    def list_usergroup(self):
        """
        Respond with the user group
        :return:
        """
        content = self.sitecmdjson('/list/usergroup')
        return self.response(content, inspect.stack()[0].function, 'List usergroups')

    def set_usergroup(self, userid, groupid):
        content = self.sitecmdjson('/upd/user/' + userid, {
            'usergroup_id': groupid
        })
        return self.response(content, inspect.stack()[0].function, 'Set usergroups')

    def list_health(self):
        """
        Health metric objects
        :return:
        """
        content = self.sitecmdjson('/stat/health')
        return self.response(content, inspect.stack()[0].function, 'Health')

    def list_dashboard(self):
        """
        List dashboards
        :return:
        """
        content = self.sitecmdjson('/stat/dashboard')
        return self.response(content, inspect.stack()[0].function, 'List dashboard')

    def list_users(self):
        """
        List users
        :return:
        """
        content = self.sitecmdjson('/list/user')
        return self.response(content, inspect.stack()[0].function, 'List users')

    def list_aps(self, mac=None):
        """
        List aps
        :return:
        """
        # TODO: It is not working with MAC different than None
        content = self.sitecmdjson('/stat/device/' + (urllib.parse.quote(mac) if mac else ''))
        return self.response(content, inspect.stack()[0].function, 'List aps')

    def list_rogueaps(self, within=24):
        """
        List rogue aps
        :param within:
        :return:
        """
        content = self.sitecmdjson('/stat/rogueap', {
            'within': within
        })
        return self.response(content, inspect.stack()[0].function, 'List rogue aps')

    def list_sites(self):
        """
        List sites
        :return:
        """
        content = self.reqjson('/api/self/sites')
        return self.response(content, inspect.stack()[0].function, 'List sites')

    def stat_sites(self):
        """
        Stat sites
        :return:
        """
        content = self.reqjson('/api/stat/sites')
        return self.response(content, inspect.stack()[0].function, 'Stat sites')

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
        return self.response(content, inspect.stack()[0].function, 'Add site')

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
        return self.response(content, inspect.stack()[0].function, 'Remove Site')

    def list_wlan_groups(self):
        """
        List wlan groups
        :return:
        """
        content = self.sitecmdjson('/list/wlangroup')
        return self.response(content, inspect.stack()[0].function, 'List Wlan groups')

    def stat_sysinfo(self):
        """
        Stat sysinfo
        :return:
        """
        content = self.sitecmdjson('/stat/sysinfo')
        return self.response(content, inspect.stack()[0].function, 'Sysinfo')

    def list_self(self):
        """
        List self
        :return:
        """
        content = self.sitecmdjson('/self')
        return self.response(content, inspect.stack()[0].function, 'Self')

    def list_networkconf(self):
        """
        List self
        :return:
        """
        content = self.sitecmdjson('/list/networkconf')
        return self.response(content, inspect.stack()[0].function, 'List network config')

    def stat_voucher(self, createtime=None):
        """
        List vouchers
        :param createtime:
        :return:
        """
        content = self.sitecmdjson('/stat/voucher', {
            'create_time': createtime
        })
        return self.response(content, inspect.stack()[0].function, 'Voucher Statistics')

    def stat_payment(self, within=None):
        """
        List vouchers
        :param within:
        :return:
        """
        content = self.sitecmdjson('/stat/voucher', {
            'within': within
        })
        return self.response(content, inspect.stack()[0].function, 'Payment Statistics')

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
        return self.response(content, inspect.stack()[0].function, 'Create Hotspot')

    def list_hotspot(self):
        """
        List hotspots
        :return:
        """
        content = self.sitecmdjson('/list/hotspotop')
        return self.response(content, inspect.stack()[0].function, 'List hotspot')

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
        return self.response(content, inspect.stack()[0].function, 'Create voucher')

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
        return self.response(content, inspect.stack()[0].function, 'Revoke Voucher')

    def list_portforwarding(self):
        """
        List portforwarding
        :return:
        """
        content = self.sitecmdjson('/list/portforward')
        return self.response(content, inspect.stack()[0].function, 'List Port Forwarding')

    def list_dynamicdns(self):
        """
        List Dynamic DNS
        :return:
        """
        content = self.sitecmdjson('/list/dynamicdns')
        return self.response(content, inspect.stack()[0].function, 'List Dynamic DNS')

    def list_portconf(self):
        """
        List Port Conf
        :return:
        """
        content = self.sitecmdjson('/list/portconf')
        return self.response(content, inspect.stack()[0].function, 'List Port Config')

    def list_extension(self):
        """
        List Extension
        :return:
        """
        content = self.sitecmdjson('/list/extension')
        return self.response(content, inspect.stack()[0].function, 'List Extension')

    def list_settings(self):
        """
        List Settings
        :return:
        """
        # TODO: Set settings to be implemented
        content = self.sitecmdjson('/get/setting')
        return self.response(content, inspect.stack()[0].function, 'List settings')

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
        return self.response(content, inspect.stack()[0].function, 'Restart AP')

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
        return self.response(content, inspect.stack()[0].function, 'Disable AP')

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
        return self.response(content, inspect.stack()[0].function, 'Locate AP')

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
        return self.response(content, inspect.stack()[0].function, 'Locate AP')

    def site_ledson(self):
        """
        All AP Leds on
        :return:
        """
        content = self.sitecmdjson('/set/setting/mgmt', {
            'led_enabled': True
        })
        return self.response(content, inspect.stack()[0].function, 'Site Leds on')

    def site_ledsoff(self):
        """
        All AP Leds off
        :return:
        """
        content = self.sitecmdjson('/set/setting/mgmt', {
            'led_enabled': False
        })
        return self.response(content, inspect.stack()[0].function, 'Site Leds off')

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
        return self.response(content, inspect.stack()[0].function, 'AP Radio Settings')

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
        return self.response(content, inspect.stack()[0].function, 'Guest Login Settings')

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
        return self.response(content, inspect.stack()[0].function, 'Rename AP')

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
        return self.response(content, inspect.stack()[0].function, 'Set WLAN Settings')

    def list_events(self):
        """
        List the events
        :return:
        """
        content = self.sitecmdjson('/stat/event')
        return self.response(content, inspect.stack()[0].function, 'List Events')

    def list_wlanconf(self):
        """
        List wlan config
        :return:
        """
        content = self.sitecmdjson('/list/wlanconf')
        return self.response(content, inspect.stack()[0].function, 'List WLAN Conf')

    def get_wlanconf(self):
        """
        get wlan config
        :return:
        """
        content = self.sitecmdjson('/rest/wlanconf')
        return self.response(content, inspect.stack()[0].function, 'Get WLAN Conf')


    def list_alarms(self):
        """
        List the alarms
        :return:
        """
        content = self.sitecmdjson('/list/alarm')
        return self.response(content, inspect.stack()[0].function, 'List Alarms')

    def set_ap_led(self, ap_id, led_override="default"):
        """
        Override led per device
        :param led_override: options on, off, default
        :param ap_id:
        :return:
        """
        content = self.sitecmdjson('/rest/device/'+str(ap_id), {
            'led_override': led_override
        })
        return self.response(content, inspect.stack()[0].function, 'AP Led')

    def set_ap_name(self, ap_id, name=None):
        """
        Override name per device
        :param name:
        :param ap_id:
        :return:
        """
        content = self.sitecmdjson('/rest/device/'+str(ap_id), {
            'name': name
        }, method='PUT')
        return self.response(content, inspect.stack()[0].function, 'Set AP Name')

    def set_ap_wireless(self, ap_id, radio="ng", channel="auto", ht=20, min_rssi=-94, min_rssi_enabled=False,
                        antenna_gain=6, tx_power_mode="auto"):
        """
        Set parameters to a wireless AP
        :param ap_id:
        :param radio:
        :param channel:
        :param min_rssi:
        :param ht:
        :param min_rssi_enabled:
        :param antenna_gain:
        :param tx_power_mode:
        :return:
        """
        content = self.sitecmdjson('/rest/device/'+str(ap_id), {
            "radio_table": [
                {
                    "antenna_gain": antenna_gain,
                    "channel": channel,
                    "radio": radio,
                    "ht": ht,
                    "min_rssi": min_rssi,
                    "min_rssi_enabled": min_rssi_enabled,
                    "tx_power_mode": tx_power_mode
                }
            ]
        }, method='PUT')
        return self.response(content, inspect.stack()[0].function, 'Set AP Wireless Settings')

    def status(self):
        """
        Retrieve status
        :return:
        """
        content = self.reqjson('/status')
        return self.response(content, inspect.stack()[0].function, 'Status')

    def set_ap_network(self, ap_id, type="dhcp", ip="192.168.1.6", netmask="255.255.255.0", gateway="192.168.1.1", dns1="8.8.8.8", dns2="8.8.4.4"):
        """
        Configure network
        :param ap_id:
        :param type:
        :param ip:
        :param netmask:
        :param gateway:
        :param dns1:
        :param dns2:
        :return:
        """
        content = self.sitecmdjson('/rest/device/' + str(ap_id), {
            "config_network": [
                {
                    "type": type,
                    "ip": ip,
                    "netmask": netmask,
                    "gateway": gateway,
                    "dns1": dns1,
                    "dns2": dns2
                }
            ]
        }, method='PUT')
        return self.response(content, inspect.stack()[0].function, 'AP Network Config')

    def request_spectrumscan(self, mac):
        """
        Request spectrum scan
        :param mac:
        :return:
        """
        content = self.sitecmdjson('/cmd/devmgr', {
            "cmd": "spectrum-scan",
            "mac": mac
        })
        return self.response(content, inspect.stack()[0].function, 'Request Spectrum Scan')

    def set_site_descr(self, description):
        """
        Set site description
        :param description:
        :return:
        """
        content = self.sitecmdjson('/cmd/sitemgr', {
            "cmd": "update-site",
            "desc": description
        })
        return self.response(content, inspect.stack()[0].function, 'Site Description')

    def set_site_settings(self, gen_id, site_id, advanced=True, alerts=True, auto_upgrade=True, key="mgmt",
                          led_enabled=True, x_ssh_username="ubnt", x_ssh_password="UBNT",
                          x_ssh_md5passwd = "$1$PiGDOzRF$GX49UVoQSqwaLgXu/Cuvb/"):
        """
        Site settings
        :param gen_id:
        :param site_id:
        :param advanced:
        :param alerts:
        :param auto_upgrade:
        :param key:
        :param led_enabled:
        :param x_ssh_username:
        :param x_ssh_password:
        :param x_ssh_md5passwd:
        :return:
        """
        content = self.sitecmdjson('/set/setting/mgmt/'+str(gen_id), {
            "_id": str(gen_id),
            "advanced_feature_enabled": advanced,
            "alert_enabled": alerts,
            "auto_upgrade": auto_upgrade,
            "key": key,
            "led_enabled": led_enabled,
            "site_id": site_id,
            "x_ssh_username": x_ssh_username,
            "x_ssh_password": x_ssh_password,
            "x_ssh_md5passwd": x_ssh_md5passwd
        })
        return self.response(content, inspect.stack()[0].function, 'Set Site Settings')
