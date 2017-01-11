#from UnifiAPI.UnifiAPI import UnifiAPI
#
#u = UnifiAPI(username='ubnt', password='UBNT', debug=True)
##d = u.stat_sessions()
##print (d['data'][0]['mac'])
##d = u.stat_sta_sessions_latest(d['data'][0]['mac'])
##print (d)
##d = u.create_hotspot('myhottyspotty','myhottyspotty','note to note')
##d = u.set_ap_wireless('5853dd90e4b03771018a974e', radio="ng", channel=7)
##d = u.request_spectrumscan('80:2a:a8:89:05:38')
#
##d = u.list_hotspot2()
##print(d)
#
#d = u.add_wlanconf("MWN-Exp", wlangroup_id="5853dc2ae4b03771018a9741")
#print(d)

from UnifiAPI.CloudAPI import CloudAPI

c = CloudAPI(username='sestest', password='sestest123', debug=True)
c.login()
d = c.devices()
print("\n\nXXX:%s\n\n"%d)
d = c.launch_dashboard("802aa88d52c70000000001eb455b0000000001fca01600000000575e1cf6")
print("\n\nYYY:%s\n\n"%d)
c.logout()
print(c)
