
# import libraries:

#!pip install feedparser
import feedparser
import pandas as pd

# user input -- will probably need to be changed by SEI team to fit this into an app:

print('Please type "A" to use archived data feed WITH an active storm,')
print('"B" to use archived feed with NO storm, or "C" to use current live feed:')
feed = input()
if feed=='A':
    feedpath = "./archive_feed"
elif feed=='B':
    feedpath = "./nostormfeed"
elif feed=='C':
    feedpath = "https://www.nhc.noaa.gov/index-at.xml"
else:
    print('Error -- please enter either A, B, or C.')
    
print('Please type an output filename')
filename = input()
if filename[-4:]!='.csv':
    print('Note: adding ".csv" to the filename')
    filename +='.csv'

# end user input section.


# read in RSS feed and get titles:
NewsFeed = feedparser.parse(feedpath)
N = len(NewsFeed.entries)
titles = [e.title for e in NewsFeed.entries]

# check for "Public Advisory" in titles list. If it's not there; there is no current storm in the feed
currentadv = [n for n in range(N) if 'Public Advisory' in titles[n]]

# case where no current storm:
if len(currentadv)==0:
    current = ''
    currentinfo = pd.DataFrame([{
            'datetime':           'NO CURRENT STORM',
            'current_latitude':   'NO CURRENT STORM',
            'current_longitude':  'NO CURRENT STORM',
            'winds_mph':          'NO CURRENT STORM',
            'storm_category':     'NO CURRENT STORM',
            'pressure_mbar':      'NO CURRENT STORM',
            'radius':             'NO CURRENT STORM',
            'time_of_landfall':   'NO CURRENT STORM',
            'movement_direction': 'NO CURRENT STORM',
            'movement_speed':     'NO CURRENT STORM',
            'watch_updates':      'NO CURRENT STORM',
            'warning_updates':    'NO CURRENT STORM',
            'alerts_summary':     'NO CURRENT STORM'
        }])

# case of one or more storms:
else:
    entries = []
    # loop over whatever storms there are -- usually just one:
    for n in range(len(currentadv)):
        # pull off the advisory text, do preliminary cleaning:
        currentadv = currentadv[n]
        current = ''.join(NewsFeed.entries[currentadv].summary.split('\n'))
        current = current.replace('--','')
        current = ''.join([c.upper() for c in current])
        
        # find the center pressure (mbar) and the wind speed text:
        pressure = current.split('PRESSURE...')[1].split('...')[0]
        winds = current.split('WINDS...')[1].split('...')[0]
        
        # convert the wind speed text to numberic value, and then use that to define the storm category
        # Using the Saffir-Simpson scale for hurricanes. Reference here : https://www.nhc.noaa.gov/aboutsshws.php
        windval = int(winds.split(' ')[0])
        if windval>=157:   category = 'Cat 5 Hurricane' 
        elif windval>=130: category = 'Cat 4 Hurricane'
        elif windval>=111: category = 'Cat 3 Hurricane'
        elif windval>=96:  category = 'Cat 2 Hurricane'
        elif windval>=74:  category = 'Cat 1 Hurricane'
        elif windval>=39:  category = 'Tropical Storm'
        else:              category = 'Subtropical'

        # radius is pulled from a different section, "description" instead of "summary":    
        chk0 = ''.join(NewsFeed.entries[currentadv].description.split('\n'))
        chk0 = ''.join([c.upper() for c in chk0])
        # if there is no info for the storm raius, use 300 mi as the default, as that is a typical value
        # https://www.weather.gov/source/zhu/ZHU_Training_Page/tropical_stuff/hurricane_anatomy/hurricane_anatomy.html
        defaultradius = 300
        # text can vary - looking for either "radius", "radii", "diameter" or "extend outward" 
        # Not just "extend" because that might mean time instead of space
        if 'RADI' in chk0:
            wrd = 'RADI'
        elif 'DIAMETER' in chk0:
            wrd = 'DIAMETER'
        elif 'EXTEND OUTWARD' in chk0:
            wrd = 'EXTEND OUTWARD'
        else: 
            wrd = ''
        if wrd != '':
            chk = chk0.split(wrd)[1].split(' ')
            nums = [n for n in range(len(chk)) if chk[n].isdigit()]
            if len(nums)>0: 
                firstnum = nums[0]
                radius = int(chk[firstnum])
                # divide by 2 if diameter was provided instead of radius:
                if wrd == 'DIAMETER': radius = radius/2
                # convert to miles if radius was given in km instead:
                unit = chk[firstnum+1]
                if unit[0:2]=='KM': radius *= 0.621371
            else:
                radius = defaultradius
        else:
            radius = defaultradius

        # projected time of landfall is a text string in the "Forecast Discussion" section:
        forecastdis = [n for n in range(N) if 'Forecast Discussion' in titles[n]]
        if len(forecastdis)>0:
            forecastdis = forecastdis[0]
            chk = ''.join(NewsFeed.entries[forecastdis].summary.split('\n')).split('. ')
            # need noth "LANDFALL" and an indication of time, or else it might be a statement of coastal erosion expected within 
            # a certain distance of landfall
            # if there is no such string, save a default statement
            timingtext = [c for c in chk if ('LANDFALL' in c) and (('MORNING' in c) or ('AFTERNOON' in c) or ('EVENING' in c) or ('NIGHT' in c))]
            if len(timingtext)>0:
                timingtext = timingtext[0]
            else:
                timingtext = 'TIME OF LANDFALL UNKNOWN'
        else:
            timingtext = 'TIME OF LANDFALL UNKNOWN'
            
        # get the current location of the storm center:
        location = current.split('LOCATION...')[1].split(' ABOUT')[0].split(' ')
        latitude = location[0]
        longitude = location[1]

        # get the time of the advisory:
        issuetime = current.split('ISSUED AT ')[1].split(' <PRE')[0]

        # get the projected path direction and speed (does NOT include the cone of uncertainty) :
        movement = current.split('MOVEMENT...')[1].split('...')[0].split(' OR ')[1].split(' AT ')
        pathdirection = movement[0]
        pathspeed = movement[1]

        # pull the warning, watch, and summary text strings:
        warningtext = current.split('CHANGES WITH THIS ADVISORY... ')[1].split(' DISCUSSION')[0]
        warningtext = warningtext.replace('U.S.','US')
        warningtext = warningtext.replace('...','-')
        warningtext = warningtext.replace(' A TROPICAL STORM WARNING MEANS THAT TROPICAL STORM CONDITIONS ARE EXPECTED SOMEWHERE WITHIN THE WARNING AREA WITHIN 36 HOURS.','')
        warningtext = warningtext.replace(' A TROPICAL STORM WATCH MEANS THAT TROPICAL STORM CONDITIONS ARE POSSIBLE WITHIN THE WATCH AREA-GENERALLY WITHIN 48 HOURS.','')
        warningtext = warningtext.replace(' A HURRICANE WARNING MEANS THAT HURRICANE CONDITIONS ARE EXPECTED SOMEWHERE WITHIN THE WARNING AREA WITHIN 36 HOURS.','')
        warningtext = warningtext.replace(' A HURRICANE WATCH MEANS THAT HURRICANE CONDITIONS ARE POSSIBLE WITHIN THE WATCH AREA-GENERALLY WITHIN 48 HOURS.','')
        warningtext = warningtext.replace(' FOR STORM INFORMATION SPECIFIC TO YOUR AREA-INCLUDING POSSIBLE INLAND WATCHES AND WARNINGS-PLEASE MONITOR PRODUCTS ISSUED BY YOUR LOCAL NATIONAL WEATHER SERVICE FORECAST OFFICE.','')
        alerts = warningtext.split('.')
        summarytext   = ''.join([c for c in alerts if ('SUMMARY' in c)])
        watchtext   = ''.join([c for c in alerts if ('WATCH' in c) and ('SUMMARY' not in c)])
        warningtext = ''.join([c for c in alerts if ('WARNING' in c) and ('SUMMARY' not in c)])
        if (watchtext=='') and (warningtext==''): summarytext = 'NO CHANGES: ' + summarytext

        # compile data:
        entries.append({
            'datetime':           issuetime,
            'current_latitude':   latitude,
            'current_longitude':  longitude,
            'winds_mph':          winds,
            'storm_category':     category,
            'pressure_mbar':      pressure,
            'radius':             radius,
            'time_of_landfall':   timingtext,
            'movement_direction': pathdirection,
            'movement_speed':     pathspeed,
            'watch_updates':      watchtext,
            'warning_updates':    warningtext,
            'alerts_summary':     summarytext
        })
    currentinfo = pd.DataFrame(entries)

# save data:
currentinfo.to_csv('./'+filename, index=False)

