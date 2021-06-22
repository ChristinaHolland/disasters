#!pip install feedparser
import feedparser
import pandas as pd

print('Please type "A" to use archived data feed WITH an active storm, "B" to use archived feed with NO storm, or "C" to use current live feed:')
feed = input()
if feed=='A':
    NewsFeed = feedparser.parse("./archive_feed")
elif feed=='B':
    NewsFeed = feedparser.parse("./nostormfeed")
elif feed=='C':
    NewsFeed = feedparser.parse("https://www.nhc.noaa.gov/index-at.xml")
else:
    print('Error -- please enter either A, B, or C.')
    
print('Please type an output filename')
filename = input()
if filename[-4:]!='.csv':
    print('Note: adding ".csv" to the filename')
    filename +='.csv'
    
N = len(NewsFeed.entries)
titles = [e.title for e in NewsFeed.entries]



currentadv = [n for n in range(N) if 'Public Advisory' in titles[n]]
if len(currentadv)==0:
    current = ''
    
    currentinfo = pd.DataFrame([{
            'datetime': '',
            'current_latitude': '',
            'current_longitude': '',
            'winds_mph': '',
            'storm_category': 'NO CURRENT STORM',
            'pressure_mbar': '',
            'movement_direction': '',
            'movement_speed': '',
            'watch_updates': '',
            'warning_updates': '',
            'alerts_summary': ''
        }])

else:
    entries = []
    for n in range(len(currentadv)):
        currentadv = currentadv[n]
        current = ''.join(NewsFeed.entries[currentadv].summary.split('\n'))
        current = current.replace('--','')
        current = ''.join([c.upper() for c in current])

        pressure = current.split('PRESSURE...')[1].split('...')[0]
        winds = current.split('WINDS...')[1].split('...')[0]
        windval = int(winds.split(' ')[0])

        if windval>=157:   category = 'Cat 5 Hurricane' 
        elif windval>=130: category = 'Cat 4 Hurricane'
        elif windval>=111: category = 'Cat 3 Hurricane'
        elif windval>=96:  category = 'Cat 2 Hurricane'
        elif windval>=74:  category = 'Cat 1 Hurricane'
        elif windval>=39:  category = 'Tropical Storm'
        else:              category = 'Subtropical'

        location = current.split('LOCATION...')[1].split(' ABOUT')[0].split(' ')
        latitude = location[0]
        longitude = location[1]

        issuetime = current.split('ISSUED AT ')[1].split(' <PRE')[0]

        movement = current.split('MOVEMENT...')[1].split('...')[0].split(' OR ')[1].split(' AT ')
        pathdirection = movement[0]
        pathspeed = movement[1]

        warningtext = current.split('CHANGES WITH THIS ADVISORY... ')[1].split(' DISCUSSION')[0]
        warningtext = warningtext.replace('U.S.','US')
        warningtext = warningtext.replace('...','-')
        warningtext = warningtext.replace(' A TROPICAL STORM WARNING MEANS THAT TROPICAL STORM CONDITIONS ARE EXPECTED SOMEWHERE WITHIN THE WARNING AREA WITHIN 36 HOURS.','')
        warningtext = warningtext.replace(' A TROPICAL STORM WATCH MEANS THAT TROPICAL STORM CONDITIONS ARE POSSIBLE WITHIN THE WATCH AREA-GENERALLY WITHIN 48 HOURS.','')
        warningtext = warningtext.replace(' FOR STORM INFORMATION SPECIFIC TO YOUR AREA-INCLUDING POSSIBLE INLAND WATCHES AND WARNINGS-PLEASE MONITOR PRODUCTS ISSUED BY YOUR LOCAL NATIONAL WEATHER SERVICE FORECAST OFFICE.','')

        alerts = warningtext.split('.')
        summarytext   = ''.join([c for c in alerts if ('SUMMARY' in c)])
        watchtext   = ''.join([c for c in alerts if ('WATCH' in c) and ('SUMMARY' not in c)])
        warningtext = ''.join([c for c in alerts if ('WARNING' in c) and ('SUMMARY' not in c)])
        if (watchtext=='') and (warningtext==''): summarytext = 'NO CHANGES: ' + summarytext

        entries.append({
            'datetime': issuetime,
            'current_latitude': latitude,
            'current_longitude': longitude,
            'winds_mph': winds,
            'storm_category': category,
            'pressure_mbar': pressure,
            'movement_direction': pathdirection,
            'movement_speed': pathspeed,
            'watch_updates': watchtext,
            'warning_updates': warningtext,
            'alerts_summary': summarytext
        })
    currentinfo = pd.DataFrame(entries)
    
currentinfo.to_csv('./'+filename, index=False)

print('Data saved to ./' + filename)