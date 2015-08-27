### HYPEMEUP.PY v1.0 ###
### BY GEORGE UTSIN AND EDWARD LU ###
### stuff
### IMPORT THE LIBS ###

# WOLOWOLOWOLO

import requests, json, urllib, urllib2, cookielib, re, os, mutagen, sys
from mutagen.mp3 import MP3
from mutagen.id3 import TOPE, TSO2, TOA, TIT2, TSOT, ID3, APIC, error

### REMOVES UNWANTED AND NON-ASCII CHARACTERS ###

def createQueryFrom(artist, title, char):

    query = artist + " " + title
    query_arr = query.split(" ")

    ### COULD MAKE AN ARRAY OF CHARS TO REMOVE BUT THIS BLOCK IS SEXIER ###

    add = ""
    for q in query_arr:
        q = q.replace("(", "")
        q = q.replace(")", "")
        q = q.replace("&", "")
        q = q.replace(".", "")
        q = re.sub('[^A-Za-z0-9]+','', q)
        if q != "":
            add = add + char + q

    return add

### DOWNLOADS ALBUM ARTWORK FROM SOUNDCLOUD ###

def downloadArtFor(artist, title):

    ### PARSE JSON FOR SOUNDCLOUD API ###

    query = createQueryFrom(artist, title, "%20")
    site = "http://api.soundcloud.com/tracks.json?q="
    url = site + query[3:]

    response = urllib.urlopen(url)
    data = json.loads(response.read())

    ### SUPER HACKY HARDCODING RIGHT HERE ###

    art_url =  data[0]["artwork_url"]
    art_url = art_url.replace("large.jpg", "t500x500.jpg")
    art_url = art_url.replace("https:", "http:")
    art_name = artist + " - " + title + ".jpg"

    urllib.urlretrieve(art_url, art_name)

### DOWNLOADS THE SONG ###

def downloadSong(artist, title, query):
    
    ### REACH MYFREEMP3 PAGE BUT WHY DO YOU NEED COPIES BRO ###

    artistCopy = artist
    titleCopy = title
    songName = artistCopy + " - " + titleCopy + ".mp3"
    artist.replace(" ","+")
    title.replace(" ","+")
    downloadComplete = 1
    
    site = query
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'utf-8',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

    req = urllib2.Request(site, headers=hdr)

    try:
        page = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e.fp.read()
        return 0

    content = page.read()
    
    pattern = "<a rel=\"nofollow\" class=\"dw\" href=\"#\" onClick=\"window.open\('(.*?)', '_blank'\)\" >Download</a>"
    m = re.search(pattern, content)
    if m:
        newsite = m.group(1)
        print "Searching..."
    else:
        print "Nothing found for: " + artist + " - " + title
        return 0

    ### REACH SAFEURL PAGE ###

    site = newsite
    req = urllib2.Request(site, headers=hdr)

    try:
        page = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e.fp.read()
        return 0

    content = page.read()

    pattern = "window.open\(\"(.*?) \"\);"
    m = re.search(pattern, content)
    if m:
        filelink = m.group(1)
        print "Beginning download of " + songName
    else:
        print "Nothing found"
        return 0

    r = requests.get(filelink)
    with open(songName, "wb") as code:
        code.write(r.content)
                    
    print "Download Complete!"
    
    from mutagen.easyid3 import EasyID3
    try:
        audio = ID3(songName)
        audio.delete()
        meta = EasyID3(songName)
        #print "wat"
    except mutagen.id3.ID3NoHeaderError:
        meta = mutagen.File(songName, easy=True)
        meta.add_tags()
        meta["title"] = u""+titleCopy
        meta["titlesort"] = u""+titleCopy
        meta["artist"] = u""+artistCopy
        meta["performer"] = u""+artistCopy
        meta["albumartistsort"] = u""+artistCopy
        meta["artistsort"] = u""+artistCopy
        meta.save(songName, v1=2)
        print songName + " formatted!"
    
    ### GET ALBUM ART AND SET TAGS ###

    downloadArtFor(artist, title)

    audio = MP3(songName, ID3=ID3)

    try:
        audio.add_tags()
    except error:
        pass

    art_name = artist + " - " + title + ".jpg"

    audio.tags.add(
        APIC(
            encoding=3,
            mime='image/jpg',
            type=3,
            desc=u'Cover',
            data=open(art_name).read()
        )
    )

    ### DOESN'T DO SHIT FOR ITUNES ###

    audio.tags.add(TOPE(3, artist))
    audio.tags.add(TSO2(3, artist))
    audio.tags.add(TOA(3, artist))

    audio.tags.add(TIT2(3, title))
    audio.tags.add(TSOT(3, title))

    audio.save(v2_version=3)
    os.remove(art_name)

    print "Album info set!"
    
    return downloadComplete

### RETURNS FULL SONG LIST FOR A HYPEM USER ###

def parseJsonFor(username):

    ### CHECK IF SONGS ARE ALREADY DOWNLOADED ###

    full_arr = []
    query_arr = []

    if not os.path.exists('SONG-LIBRARY.txt'):
        open('SONG-LIBRARY.txt', 'w').close() 

    songs_file = open('SONG-LIBRARY.txt', 'r+')
    songs_list = songs_file.read()

    if songs_list != "":
        songs_arr = songs_list.split("\n")
    else:
        songs_arr = []

    ### PARSE JSON FEED ###

    page = 1
    while page > 0:
        url = "http://hypem.com/playlist/loved/" + username + "/json/" + str(page) + "/data.js"
        try:
            response = urllib2.urlopen(url)
            response_copy = urllib2.urlopen(url)
            content = response_copy.read()

            if content[2:9] == "version":
                data = json.loads(response.read())
                page = page + 1

                list_length = len(data) - 1

                for l in range(0, list_length):
                    l = list_length-1-l

                    title = data[str(list_length-1-l)]["title"]
                    artist = data[str(list_length-1-l)]["artist"]
                    full = artist + " - " + title

                    if full.encode('utf-8') not in songs_arr:
                        full_arr.insert(0, full)
            else:
                page = -1
        except urllib2.HTTPError, e:
            page = -1

    return full_arr

### WRITES THE SONGLIST TO LOCAL TEXT FILE ###

def writeFileFor(username):

    full_arr = parseJsonFor(username)

    for full in full_arr:
        with open("SONG-LIBRARY.txt", "a") as songs_file:
            songs_file.write(full.encode('utf-8') + "\n")

### DOWNLOADS ALL SONGS FOR A USER ###

def downloadSongsFor(username):

    full_arr = parseJsonFor(username)

    for full in full_arr:
        artist = full.split(" - ")[0]
        title = full.split(" - ")[1]
        query = createQueryFrom(artist, title, "+")

        site = "http://www.myfreemp3.biz/mp3/"
        site = site + query[1:]

        artist = full.split(" - ")[0]
        title = full.split(" - ")[1]

        try:
            success = downloadSong(artist, title, site)
        except:
            print "Oops, some shit went down"
            print "We couldn't download: " + full 
            success = 0
        if success == 1:
            with open("SONG-LIBRARY.txt", "a") as songs_file:
                songs_file.write(full.encode('utf-8') + "\n")

def downloadSongsFromFile():
    print "swag"
    ### DO SHIT ###

def downloadSongsFromHypem():

    if not os.path.exists('SONG-LIBRARY.txt'):
        open('SONG-LIBRARY.txt', 'w').close()
        name = raw_input("Enter your hypem username pls bro: ")
        print "Fetching your songs..."
        with open("SONG-LIBRARY.txt", "a") as songs_file:
            songs_file.write(name.encode('utf-8') + "\n")

        ### JSON FETCH DOESN'T ALWAYS HIT FOR SOME DUMB AF REASON SO MULITPLE CALLS FOR REDUNDANCY ###

        writeFileFor(name)
        writeFileFor(name)
        writeFileFor(name)

        print "Please delete all the songs you want to download from the library now\nThe library is located in SONG-LIBRARY.txt, should be beside the exe file"
        response = raw_input("Would you like to download the songs now? (y/n)")
        if response == u'y':
            print "^Disregard that error above :)"
            downloadSongsFor(name.decode("utf-8"))
        else:
            sys.exit()
    else:
        songs_file = open('SONG-LIBRARY.txt', 'r+')
        songs_list = songs_file.read()
        name = ""
        if songs_list != "":
            songs_arr = songs_list.split("\n")
            name = songs_arr[0]
        print name.decode("utf-8")
        downloadSongsFor(name.decode("utf-8"))

### YOU YOU ARE A BAE BAE (YOU ARE YOU ARE) ###

downloadSongsFromHypem()
