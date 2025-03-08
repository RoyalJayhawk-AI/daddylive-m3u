import xml.etree.ElementTree as ET
import random
import uuid
import fetcher
import json
import os
import datetime
import pytz

#generate static list of static channel names
#get schedule JSON
#parse wanted tags
    #build channel list
    #build guide

NUM_CHANNELS        = 400
DADDY_JSON_FILE     = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE    = "daily.m3u8"
EPG_OUTPUT_FILE     = "daily.xml"
LOGO                = "https://raw.githubusercontent.com/JHarding86/daddylive-m3u/refs/heads/main/hardingtv.png"

mStartTime = 0
mStopTime = 0

def generate_unique_ids(count, seed=42):
    random.seed(seed)
    ids = []
    for _ in range(count):
        id_str = str(uuid.UUID(int=random.getrandbits(128)))  # Generate a unique UUID
        ids.append(id_str)
    return ids

def loadJSON(filepath):
    # Open and read the JSON file
    with open(filepath, 'r', encoding='utf-8') as file:
        json_object = json.load(file)

    # Print the Python dictionary
    # print(json_object)

    return json_object

def createSingleChannelEPGData(UniqueID, tvgName):
     #Creating M3U8 Data
    xmlChannel      = ET.Element('channel')
    xmlDisplayName  = ET.Element('display-name')
    xmlIcon         = ET.Element('icon')

    xmlChannel.set('id', UniqueID)
    xmlDisplayName.text = tvgName
    xmlIcon.set('src', LOGO)

    xmlChannel.append(xmlDisplayName)
    xmlChannel.append(xmlIcon)

    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName, description):
    #Creating EPG Data
    programme   = ET.Element('programme')
    title       = ET.Element('title')
    desc        = ET.Element('desc')

    programme.set('start', startTime + " +0000")
    programme.set('stop', stopTime + " +0000")
    programme.set('channel', UniqueID)

    title.text = channelName

    desc.text = description

    programme.append(title)
    programme.append(desc)

    return programme

def addChannelsByLeagueSport(leagueSportTuple):
    for day, value in dadjson.items():
        try:
            # print("NEW DAY\n\n\n")
            for leagueSport in leageSportTuple:
                sport = dadjson[f"{day}"][leagueSport["sport"]]
                for game in sport:
                    if leagueSport["league"] in game["event"]:
                        print(game["event"])
                    
                        for channel in game["channels"]:
                            #Creating Time Data
                            date_time = day.replace("th ", " ").replace("rd ", " ").replace("st ", " ").replace("nd ", " ").replace("Dec Dec", "Dec")
                            date_time = date_time.replace("-", game["time"] + " -")
                            # Parse the cleaned date string into a datetime object
                            date_format = "%A %d %b %Y %H:%M - Schedule Time UK GMT"
                            start_date = datetime.datetime.strptime(date_time, date_format)
                            global mStartTime
                            mStartTime = start_date.strftime("%Y%m%d000000")
                            stop_date = start_date + datetime.timedelta(days=2)
                            global mStopTime
                            mStopTime = stop_date.strftime("%Y%m%d000000")
                            
                            format_12_hour = start_date.strftime("%m/%d/%y")
                            start_date = start_date - datetime.timedelta(hours=7)

                            startHour = start_date.strftime("%I:%M %p") + " (MST)"
                            format_12_hour = format_12_hour + " - " + startHour

                            UniqueID    = unique_ids.pop(0)
                            try:
                                channelName = game["event"] + " " + format_12_hour + " " + channel["channel_name"]
                            except TypeError:
                                print("Ill formatted JSON, skipping this channel for this game.")
                                continue
                            
                            channelID   = f"{channel['channel_id']}"

                            global channelCount
                            tvgName = "OpenChannel" + str(channelCount).zfill(3)
                            tvLabel = tvgName
                            channelCount = channelCount + 1

                            # tvgName = channelName
                            # tvLabel = channel["channel_name"]

                            with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
                                file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="USA (DADDY LIVE)", {tvLabel}\n')
                                file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channelID}/index.m3u8\n")
                                file.write('\n')

                            #Creating M3U8 Data
                            xmlChannel = createSingleChannelEPGData(UniqueID, tvgName)
                            root.append(xmlChannel)

                            programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, channelName, "No Description")
                            root.append(programme)
        except KeyError as e:
            print(f"KeyError: {e} - One of the keys {day} or {leagueSportTuple} does not exist.")

channelCount = 0
unique_ids = generate_unique_ids(NUM_CHANNELS)

fetcher.fetchHTML(DADDY_JSON_FILE, "https://thedaddy.to/schedule/schedule-generated.json")

dadjson = loadJSON(DADDY_JSON_FILE)

if os.path.isfile(M3U8_OUTPUT_FILE):
    os.remove(M3U8_OUTPUT_FILE)

root = ET.Element('tv')

#league sport tuple
leageSportTuple = []
leageSportTuple.append({"league":"NHL", "sport":"Ice Hockey"})
leageSportTuple.append({"league":"NFL", "sport":"Am. Football"})

addChannelsByLeagueSport(leageSportTuple)

#Fill out the remaining channels so that you don't have to re-add the channels list into plex
for id in unique_ids:
    with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
        channelNumber = str(channelCount).zfill(3)
        tvgName = "OpenChannel" + channelNumber
        file.write(f'#EXTINF:-1 tvg-id="{id}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="USA (DADDY LIVE)", {tvgName}\n')
        file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channelNumber}/index.m3u8\n")
        file.write('\n')
        channelCount += 1

    xmlChannel = createSingleChannelEPGData(id, tvgName)
    root.append(xmlChannel)

    programme = createSingleEPGData(mStartTime, mStopTime, id, "No Programm Available", "No Description")
    root.append(programme)

tree = ET.ElementTree(root)
tree.write(EPG_OUTPUT_FILE, encoding='utf-8', xml_declaration=True)