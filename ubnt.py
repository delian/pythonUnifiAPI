import UnifiAPI

u = UnifiAPI.UnifiAPI(username='ubnt', password='UBNT', debug=True)
#d = u.stat_sessions()
#print (d['data'][0]['mac'])
#d = u.stat_sta_sessions_latest(d['data'][0]['mac'])
#print (d)
#d = u.create_hotspot('myhottyspotty','myhottyspotty','note to note')
d = u.list_alarms()
print (d)
