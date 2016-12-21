import UnifiAPI

u = UnifiAPI.UnifiAPI(username='ubnt', password='UBNT', debug=True)
d = u.stat_sessions()
#print (d['data'][0]['mac'])
#d = u.stat_sta_sessions_latest(d['data'][0]['mac'])
#print (d)
#d = u.create_hotspot('myhottyspotty','myhottyspotty','note to note')
#d = u.set_ap_wireless('5853dd90e4b03771018a974e', radio="ng", channel=7)
#d = u.request_spectrumscan('80:2a:a8:89:05:38')
print (d)
