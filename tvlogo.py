import json
import os
from bs4 import BeautifulSoup
import requests

def extract_tv_logos(filename):
    logo_dict = {}

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        print("File HTML analizzato correttamente.")

        # Trova i tag che contengono i loghi
        for item in soup.find_all('a', class_='js-navigation-open'):
            logo_name = item.text.strip().lower().replace('.png', '')
            logo_path = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/" + item['href'].split('/')[-1]

            logo_dict[logo_name] = logo_path
        
        print("Loghi trovati:", json.dumps(logo_dict, indent=2, ensure_ascii=False))

    except Exception as e:
        print("Errore durante l'estrazione dei loghi:", e)

    return logo_dict

def search_logo(channel_name, logo_dict):
    """
    Cerca il logo corrispondente al nome del canale in logo_dict.
    """
    channel_name_lower = channel_name.lower().strip()
    print(f"Cercando logo per: {channel_name_lower}")

    for key in logo_dict.keys():
        print(f"Confronto con: {key}")  # Debug

        if key in channel_name_lower:
            print(f"Trovato logo: {logo_dict[key]}")  # Debug
            return logo_dict[key]

    print("Logo non trovato, uso default.")
    return "https://raw.githubusercontent.com/emaschi123/eventi/refs/heads/main/ddlive.png"

def download_logo(item, output_dir):
    if item and 'name' in item and 'path' in item:
        logo_name = item['name']
        logo_path = item['path']

        base_url = "https://github.com/tv-logo/tv-logos/tree/main/countries/italy"
        logo_url = base_url + logo_path

        os.makedirs(output_dir, exist_ok=True)

        try:
            response = requests.get(logo_url, stream=True)
            response.raise_for_status()

            filepath = os.path.join(output_dir, logo_name)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Logo scaricato con successo: {logo_name}")
        except requests.exceptions.RequestException as e:
            print(f"Errore durante il download del logo {logo_name}: {e}")
    else:
        print("Dati non validi per il download del logo.")

# Esempio di utilizzo (da chiamare dallo script principale)
if __name__ == '__main__':
    filename = 'tv_logos_page.html'  # Sostituisci con il nome del file HTML
    payload = extract_payload_from_file(filename)

    if payload:
        search_term = 'rai 1'  # Termine di ricerca di esempio
        results = search_tree_items(search_term, payload)

        if results:
            print(f"Trovate {len(results)} corrispondenze:")
            for item in results:
                print(item['name'])
                download_logo(item, 'output_logos')  # Sostituisci 'output_logos' con la tua directory
        else:
            print(f"Nessuna corrispondenza trovata per '{search_term}'.")
