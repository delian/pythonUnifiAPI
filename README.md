# Python UnifiAPI implementation
Python3 port of UniFi-API-Browser API with small extensions

<b>Usage:</b>

    from UnifiAPI.UnifiAPI import UnifiAPI
    u = UnifiAPI(username='ubnt', password='UBNT', debug=True)
    d = u.stat_sessions()
    print (d['data'][0]['mac'])
    d = u.stat_sta_sessions_latest(d['data'][0]['mac'])
    print (d)
    d = u.create_hotspot('myhottyspotty','myhottyspotty','note to note')
    d = u.set_ap_wireless('5853dd90e4b03771018a974e', radio="ng", channel=7)
    d = u.request_spectrumscan('80:2a:a8:55:55:58')    
    d = u.list_hotspot2()
    print(d)
    d = u.add_wlanconf("SSIDexample", wlangroup_id="5853dc2ae4b03771018a9741")
    print(d)
