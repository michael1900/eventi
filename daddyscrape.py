import os
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
import gzip
import tvlogo
import chardet
from tvlogo import extract_tv_logos


daddyLiveChannelsFileName = '247channels.html'
daddyLiveChannelsURL = 'https://thedaddy.to/24-7-channels.php'

tvLogosFilename = 'tvlogos.html'
tvLogosURL = 'https://github.com/tv-logo/tv-logos/tree/main/countries/italy'

STATIC_LOGOS = {
    "sky uno": "https://github.com/tv-logo/tv-logos/blob/main/countries/italy/sky-uno-it.png",   # Sostituisci con l'URL desiderato
    "rai 1": "https://github.com/tv-logo/tv-logos/blob/main/countries/italy/rai-1-it.png",   # Sostituisci con l'URL desiderato
    "rai 2": "https://github.com/tv-logo/tv-logos/blob/main/countries/italy/rai-2-it.png",   # Sostituisci con l'URL desiderato
    "rai 3": "https://github.com/tv-logo/tv-logos/blob/main/countries/italy/rai-3-it.png",   # Sostituisci con l'URL desiderato
    "eurosport 1": "https://github.com/tv-logo/tv-logos/blob/main/countries/spain/eurosport-1-es.png",   # Sostituisci con l'URL desiderato
    "eurosport 2": "https://github.com/tv-logo/tv-logos/blob/main/countries/spain/eurosport-2-es.png"   # Sostituisci con l'URL desiderato
}

epgs = [
    {'filename': 'epgShare1.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz'}
]

def delete_file_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f'File {file_path} deleted.')

def fetch_with_debug(filename, url):
    try:
        print(f'Downloading {url}...')
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with open(filename, 'wb') as file:
            file.write(response.content)
        
        print(f'File {filename} downloaded successfully.')
    except requests.exceptions.RequestException as e:
        print(f'Error downloading {url}: {e}')

def search_streams(file_path, keyword):
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
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

def search_channel_ids(file_path, search_string):
    id_matches = []
    try:
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                tree = ET.parse(f)
        else:
            tree = ET.parse(file_path)
        
        root = tree.getroot()
        search_words = search_string.lower().split()
        
        for channel in root.findall('.//channel'):
            channel_id = channel.get('id')
            channel_name_element = channel.find('display-name')
            channel_name = channel_name_element.text if channel_name_element is not None else ""
            
            if any(word in channel_name.lower() for word in search_words):
                id_matches.append({'id': channel_id, 'source': file_path})
    except (FileNotFoundError, ET.ParseError, gzip.BadGzipFile) as e:
        print(f'Error processing {file_path}: {e}')
    return id_matches

def search_logo(channel_name, logo_dict):
    """
    Cerca il logo corrispondente al nome del canale in logo_dict.
    Se il logo non viene trovato, restituisce un'icona predefinita.
    """
    channel_name_lower = channel_name.lower().strip()
    
    # Controllo statico
    for key, url in STATIC_LOGOS.items():
        if key in channel_name_lower:
            print(f"DEBUG: Trovato match statico per '{channel_name_lower}' -> {url}")
            return url

    for key, url in logo_dict.items():
        if key in channel_name_lower:
            print(f"DEBUG: Trovato match in logo_dict per '{channel_name_lower}' -> {url}")
            return url

    # Se nessuno corrisponde, restituisce il logo di default
    print(f"DEBUG: Nessun logo trovato per '{channel_name_lower}', uso default.")
    return "https://raw.githubusercontent.com/emaschi123/eventi/refs/heads/main/ddlive.png"

def generate_m3u8(matches, logo_dict):
    if not matches:
        print("No matches found. Skipping M3U8 generation.")
        return

    with open("out.m3u8", 'w', encoding='utf-8') as file:
        file.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/emaschi123/eventi/main/epgShare1.xml"\n')

        for channel in matches:
            channel_id = channel[0]
            channel_name = channel[1].replace("Italy", "").replace("8", "").replace("(251)", "").replace("(252)", "").replace("(253)", "").replace("(254)", "").replace("(255)", "").replace("(256)", "").replace("(257)", "").replace("HD+", "").strip()  

           # Cerca il logo nel dizionario
            tvicon_path = search_logo(channel_name, logo_dict)
            if not tvicon_path:
                tvicon_path = "https://raw.githubusercontent.com/emaschi123/eventi/refs/heads/main/ddlive.png"  

            file.write(f"#EXTINF:-1 tvg-id=\"{channel_id}\" tvg-name=\"{channel_name}\" tvg-logo=\"{tvicon_path}\" group-title=\"TV ITA\", {channel_name}\n")
            file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
            file.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n')
            file.write(f'#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
            file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channel_id}/index.m3u8\n\n")

    print("M3U8 file generated successfully.")


# Cleanup and Fetch Data
delete_file_if_exists(daddyLiveChannelsFileName)
delete_file_if_exists(tvLogosFilename)
for epg in epgs:
    delete_file_if_exists(epg['filename'])

fetch_with_debug(daddyLiveChannelsFileName, daddyLiveChannelsURL)
fetch_with_debug(tvLogosFilename, tvLogosURL)
for epg in epgs:
    fetch_with_debug(epg['filename'], epg['url'])

# Process Data
matches = search_streams(daddyLiveChannelsFileName, "italy")
logo_dict = extract_tv_logos(tvLogosFilename)  # Estrai i loghi corretti
generate_m3u8(matches, logo_dict)
