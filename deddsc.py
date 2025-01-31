from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
import json

import tvlogo
import fetcher

daddyLiveChannelsFileName = '247channels.html'
daddyLiveChannelsURL = 'https://thedaddy.to/24-7-channels.php'

tvLogosFilename = 'tvlogos.html'
tvLogosURL = 'https://github.com/tv-logo/tv-logos/tree/main/countries/italy'

matches = []

def search_streams(file_path, keyword):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                if keyword.lower() in link.text.lower():
                    href = link['href']
                    stream_number = href.split('-')[-1].replace('.php', '')
                    stream_name = link.text.strip()
                    match = (stream_number, stream_name)

                    if match not in matches:
                        matches.append(match)

    except FileNotFoundError:
        print(f'The file {file_path} does not exist.')

    return matches

def search_channel_ids(file_path, search_string, idMatches):
    idMatches = []
    search_words = search_string.lower().split()

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for channel in root.findall('.//channel'):
            channel_id = channel.get('id')
            channel_name_element = channel.find('display-name')
            channel_name = channel_name_element.text if channel_name_element is not None else ""
            print(f"Trovato canale: ID='{channel_id}', Nome='{channel_name}'")

            for word in search_words:
                xpath_query = f".//channel[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}') or contains(translate(display-name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]"
                matching_channels = root.findall(xpath_query)

                for match in matching_channels:
                    channel_id = match.get('id')
                    if channel_id and {'id': channel_id, 'source': file_path} not in idMatches:
                        idMatches.append({'id': channel_id, 'source': file_path})
                break

    except FileNotFoundError:
        print(f'The file {file_path} does not exist.')
    except ET.ParseError:
        print(f'The file {file_path} is not a valid XML file.')

    return idMatches

def print_possible_ids(possibleIds, channel):
    if possibleIds:
        print(f'0). I dont want this channel.')
        for index, match in enumerate(possibleIds):
            print(f"{index+1}). {match['id']} {match['source']}")

        while True:
            try:
                user_input = input(f"Do you want this channel? 0 = no 1 = yes ({channel[1]}):")
                if user_input == "":
                    print("Please enter a number (0 or 1).")
                    continue

                user_input = int(user_input)

                if user_input == 0:
                    return -1
                elif user_input == 1:
                    print("Searching for matches...")
                    break
                else:
                    print("Invalid input. Please enter 0 or 1.")

            except ValueError:
                print("Invalid input. Please enter a number.")
    else:
        print('No matches found.')
        return None

def delete_file_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f'File {file_path} deleted.')
        return True
    else:
        print(f'File {file_path} does not exist.')
        return False

delete_file_if_exists('out.m3u8')
delete_file_if_exists('tvg-ids.txt')

epgs = [
    {'filename': 'epgShare1.xml', 'url': 'https://xmltv.tvkaista.net/guides/raiplay.it.xml'},
    {'filename': 'epgShare2.xml', 'url': 'https://xmltv.tvkaista.net/guides/guida.tv.xml'},
    {'filename': 'epgShare3.xml', 'url': 'https://xmltv.tvkaista.net/guides/mediasetinfinity.mediaset.it.xml'},
    {'filename': 'epgShare4.xml', 'url': 'https://xmltv.tvkaista.net/guides/superguidatv.it.xml'},
    {'filename': 'epgShare5.xml', 'url': 'https://xmltv.tvkaista.net/guides/tivu.tv.xml'},
]

fetcher.fetchHTML(daddyLiveChannelsFileName, daddyLiveChannelsURL)
fetcher.fetchHTML(tvLogosFilename, tvLogosURL)

for epg in epgs:
    fetcher.fetchXML(epg['filename'], epg['url'])

search_terms = ["taly"]

payload = tvlogo.extract_payload_from_file(tvLogosFilename)
print("Payload:", payload)

for term in search_terms:
    search_streams(daddyLiveChannelsFileName, term)

print("Matches:", matches)

for channel in matches:
    word = channel[1].lower().replace('channel', '').replace('hdtv', '').replace('tv','').replace(' hd', '').replace('2','').replace('sports','').replace('1','').replace('usa','').strip()
    word = ''.join(char for char in word if char.isalnum())
    print(f"Searching for IDs for: '{word}'")
    possibleIds = []

    user_input = print_possible_ids(possibleIds, channel[1])

    if user_input == -1:
        continue

    if user_input == 1:
        print("Searching for matches...")
    else:
        continue

    for epg in epgs:
        search_channel_ids(epg['filename'], word, possibleIds)
        print(f"ID Matches for '{word}': {possibleIds}")

    logo_matches = tvlogo.search_tree_items(word, payload)

    channelID = print_possible_ids(possibleIds, channel[1])
    print("Channel ID:", channelID)
    tvicon = print_possible_ids(logo_matches, channel[1])
    print("TV Icon:", tvicon)

    if channelID != -1 and channelID is not None:
        with open("out.m3u8", 'a', encoding='utf-8') as file:
            try:
                initialPath = payload.get('initial_path', '')
                if matches.index(channel) == 0:
                    file.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/emaschi/daddylive/refs/heads/main/daily.xml"\n')
                file.write(f"#EXTINF:-1 tvg-id=\"{channelID['id']}\" tvg-name=\"{channel[1]}\" tvg-logo=\"https://raw.githubusercontent.com{initialPath}{tvicon['id']['path']}\" group-title=\"TV ITA\", {channel[1]}\n")
                file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
                file.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n')
                file.write(f'#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
                file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channel[0]}/index.m3u8\n")
                file.write('\n')

            except Exception as e:
                print(f"Errore durante la scrittura del file: {e}")

        with open("tvg-ids.txt", 'a', encoding='utf-8') as file:
                file.write(f'{channelID.get("id")}\n')

print("Number of Streams: ", len(matches))

for epg in epgs:
    if os.path.exists(epg['filename']):
        print(f"File {epg['filename']} exists.")
        with open(epg['filename'], 'r', encoding='utf-8') as f:
            epg_content = f.read()
            print(f"Contenuto di {epg['filename']}:\n{epg_content[:500]}...")
    else:
        print(f"File {epg['filename']} DOES NOT exist.")
