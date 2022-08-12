import json
import requests
import re
from texttable import Texttable
import threading
from autoDJutils import * #contains utility functions and setup code that is shared between
                          #autoDJ and setupTriggers
                          #this file MUST be imported for setupTriggers to work

def main():
    state = 0
    print('Welcome to the autoDJ scene setup utility. At any time, type "help" for a list of available commands. At any time, type "exit" to exit this utility.')
    while(state != -1): # -1 is the exit state, meaning we want to close the program
        while(state == 0): #Ready to add a new trigger or view current ones
            userInput = input('Type a command and press enter.\n')
            userInputSplit = userInput.split()
            try:
                match userInputSplit[0]:
                    case 'help':
                        table = Texttable()
                        table.header(['Command', 'Description', 'Parameters'])
                        table.add_row(['add', 'adds a new trigger at the current timestamp in the current spotify song with the current light effects', 'none'])
                        table.add_row(['listall', 'lists all the songs with current triggers', 'none'])
                        table.add_row(['list <songIndex>', 'lists all the triggers of the provided song index', 'index of song in songTriggers. Find using command listall'])
                        table.add_row(['play <songIndex>', 'plays the song and effects at the provided song index', 'index of song in songTriggers. Find using command listall'])
                        print(table.draw())

                    case 'add':
                        tempSongIndex, tempSceneName, tempTimestamp = addTrigger()
                        print("New trigger temporarily added, but not yet saved.")
                        state = 1
                    
                    case 'listall':
                        table = Texttable()
                        table.header(['Song Index', 'Song Name', '# of Triggers'])
                        for i in range(0, len(songTriggers)):
                            table.add_row([i, songTriggers[i]['name'], len(list(songTriggers[i]['scenes']))])
                        print(table.draw())
                    
                    case 'list':
                        listIndex = int(userInputSplit[1])
                        sceneList = list(songTriggers[listIndex]['scenes'])
                        table = Texttable()
                        table.header(['Trigger Number', 'Trigger Name', 'Timestamp'])
                        for i in range(0, len(sceneList)):
                            table.add_row([i, sceneList[i], convertMillis(songTriggers[listIndex]['scenes'][sceneList[i]])])
                        print(table.draw())
                    
                    case 'play':
                        playIndex = int(userInputSplit[1])
                        playID = songTriggers[playIndex]['id']
                        spotify.start_playback(spotifyDeviceID, uris=['spotify:track:'+playID])
                        t = threading.Thread(target = playSongScenes, args=(playIndex, 0), daemon=True)
                        t.start()
        
                    case 'exit':
                        state = -1

                    case _:
                        print("Invalid command. Try again")
            except:
                print("Invalid command. Try again")
        
        while(state == 1): #A new trigger has been added, but not saved
            print('Currently modifying a temporary Trigger. Type "save" to save this trigger and return to main menu.')
            userInput = input('Type "help" for a list of commands to modify this trigger. Type "exit" to close the program.\n')
            
            try:
                match userInput:
                    case 'help':
                        table = Texttable()
                        table.header(["Command", "Description"])
                        table.add_row(['test', 'plays the current trigger to allow you to verify if the timestamp is set correctly'])
                        table.add_row(['save', 'saves the trigger to the triggers file and returns to main menu'])
                        table.add_row(['discard', 'discards the current trigger and returns to main menu'])
                        table.add_row(['+', 'increases the timestamp of this trigger by 0.1 seconds'])
                        table.add_row(['+...+', 'increases the timestamp of this trigger by 0.1 seconds times the number of pluses. For example, "+++" would increase the timestamp by 0.3 seconds'])
                        table.add_row(['-', 'decreases the timestamp of this trigger by 0.1 seconds'])
                        table.add_row(['-...-', 'decreases the timestamp of this trigger by 0.1 seconds times the number of minuses'])
                        print(table.draw())

                    case 'test':
                        print('testing trigger...')
                        testTrigger(tempSongIndex, 6)

                    case 'save':
                        print("Trigger saved. Returning to main menu")
                        saveEffectsToFile()
                        state = 0

                    case 'discard':
                        print('trigger deleted. Returning to main menu')
                        deleteScene(tempSceneName)
                        songTriggers[tempSongIndex]['scenes'].pop(tempSceneName)
                        if(len(songTriggers[tempSongIndex]['scenes']) == 0):
                            IDtoRemove = songTriggers[tempSongIndex]['id']
                            idList.remove(IDtoRemove)
                            songTriggers.pop(tempSongIndex)
                        state = 0

                    case 'exit':
                        state = -1

                    case _:
                        if(userInput[0] == '+'):
                            songTriggers[tempSongIndex]['scenes'][tempSceneName] = (tempTimestamp + 100*len(userInput))
                        elif(userInput[0] == '-'):
                            songTriggers[tempSongIndex]['scenes'][tempSceneName] = (tempTimestamp - 100*len(userInput))
                        else:    
                            print('Invalid command. Try again')
            except Exception as e:
                print(e)
                print('Invalid Command. Try again')


def convertMillis(millis):
    seconds = str(int((millis/1000)%60))
    minutes = str(int((millis/(1000*60))%60))
    if(int(seconds) < 10):
        seconds = '0'+seconds
    timeString = '%s:%s' % (minutes, seconds)
    return timeString

def saveEffectsToFile():
    f = open('.\\songTriggers.json','w')
    json.dump(songTriggers, f, indent=4)
    f.close()

def addScene(sceneName):
    payload = json.dumps({'name': sceneName})
    url = "http://127.0.0.1:8888/api/scenes"
    headers = {'Content-Type': 'application/json'}
    try:
        requests.request('POST', url=url, headers=headers, data=payload)
    except Exception as e:
        print(e)

def deleteScene(sceneName):
    payload = json.dumps({'id': sceneName})
    url = "http://127.0.0.1:8888/api/scenes"
    headers = {'Content-Type': 'application/json'}
    try:
        requests.request('DELETE', url=url, headers=headers, data=payload)
    except Exception as e:
        print(e)

def setDeviceBlack(deviceID):
    payload = json.dumps(
        {
        "config": {
            "mirror": 'false',
            "color": "#000000",
            "background_color": "#000000",
            "blur": 0.0,
            "modulation_speed": 0.5,
            "modulation_effect": "sine",
            "flip": 'false',
            "speed": 1.0,
            "modulate": 'false',
            "brightness": 1.0,
            "background_brightness": 1.0
         },
        "name": "Single Color",
        "type": "singleColor"
        }
    )
    url = "http://127.0.0.1:8888/api/virtuals/"+deviceID+"/effects"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.request('POST', url=url, headers=headers, data=payload)
        responseObject = json.loads(response.text)
        responseFormatted = json.dumps(responseObject, indent = 2)
        print(responseFormatted)
    except Exception as e:
        print(e)

def addTrigger():
    try:
        currentPlayer = spotify.currently_playing()
        songID = currentPlayer['item']['id']
        songName = currentPlayer['item']['name']
        currentTimestamp = currentPlayer['progress_ms']
    except Exception as e:
        print(e)
        return

    sceneName = generateID(songName+convertMillis(currentTimestamp))
    
    inList = False
    songIndex = 0
    for i in range(0, len(idList)):
        if(songID == idList[i]):
            print('in list')
            songIndex = i
            inList = True
            songTriggers[i]['scenes'][sceneName] = currentTimestamp
            break
    if(inList == False):
        print('not in list')
        idList.append(songID)
        data = {
        "id": songID,
        "name": songName,
        "scenes": {
            sceneName:currentTimestamp
            }
        }
        songIndex = len(songTriggers)
        songTriggers.append(data)

    addScene(sceneName)
    return songIndex, sceneName, currentTimestamp

def generateID(name):
    #converts name into an ID that matches what LedFX will convert it to
    #taken straight from LedFX source code
    part1 = re.sub("[^a-zA-Z0-9]", " ", name).lower()
    return re.sub(" +", " ", part1).strip().replace(" ", "-")

def testTrigger(songIndex, triggerTime):
    playbackState = spotify.current_playback()
    currentTimestamp = playbackState['progress_ms']
    if(playbackState['is_playing'] == True):
        spotify.pause_playback(spotifyDeviceID)
    
    if((currentTimestamp - ((triggerTime/2)*1000)) < 0):
        spotify.seek_track(0, spotifyDeviceID)
    else:
        spotify.seek_track(currentTimestamp - int(triggerTime/2 * 1000), spotifyDeviceID)
    
    spotify.start_playback(spotifyDeviceID)
    t = threading.Thread(target = playSongScenes, args=(songIndex, triggerTime), daemon=True)
    t.start()
    t.join()
    spotify.pause_playback(spotifyDeviceID)
    spotify.seek_track(currentTimestamp, spotifyDeviceID)

if __name__ == "__main__":
    main()





