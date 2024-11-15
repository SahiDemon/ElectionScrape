import os
import time
import json
import requests
from glob import glob
from googletrans import Translator
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from bs4 import BeautifulSoup
import msvcrt
import win32com.client

# Configuration
webhook_url = ""
user_id = 
website_url = "https://election.adaderana.lk/general-election-2024/index.php"
base_url = "https://election.adaderana.lk/general-election-2024/"

party_map = {
    "NPPJathika Jana Balawegaya": "npp_votes",
    "SJBSamagi Jana Balawegaya": "sjb_votes",
    "NDFNew Democratic Front": "ndf_votes",
    "UDVUnited Democratic Voice": "uvd_votes",
    "SLPPSri Lanka Podujana Peramuna": "slpp_votes",
    "MJPMinority Justice Party": "mjp_votes"
}

def fetch_website_data():
    try:
        print("[INFO] Fetching website data...")
        response = requests.get(website_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request error: {e}")
        return None

def extract_division_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    rows = soup.select("table.table tbody tr")
    for row in rows:
        division = row.find("td").text.strip()
        division_link = row.find("a", href=True)['href']
        full_url = base_url + division_link
        links[division] = full_url
    return links

def extract_division_results(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidate_data = {json_key: None for json_key in party_map.values()}

    result_blocks = soup.select(".card-body > .district > .dis_ele_result > .dis_ele_result_block")
    for result in result_blocks:
        try:
            result_text = result.get_text(separator="\n").strip()
            lines = result_text.split("\n")
            if len(lines) >= 4:
                party_abbreviation = lines[0].strip()
                party_full_name = lines[1].strip()
                votes_text = lines[-1].strip()

                full_party_name = party_abbreviation + party_full_name
                if full_party_name in party_map:
                    votes = ''.join(c for c in votes_text if c.isdigit())
                    candidate_data[party_map[full_party_name]] = int(votes) if votes.isdigit() else None
        except Exception as e:
            print(f"[ERROR] Error processing result block: {e}")

    general_data = {}
    try:
        summary_table = soup.find("div", class_="total-votes-summery").find("table")
        for row in summary_table.find_all("tr"):
            label = row.find("th").text.strip().lower()
            votes = int(row.find_all("td")[0].text.replace(',', ''))
            general_data[label] = votes
    except Exception as e:
        print(f"[ERROR] Error extracting general voting summary: {e}")

    return candidate_data, general_data

def process_json_to_image(psd_file_path, district_name, vote_data, general_data):
    if not os.path.exists(psd_file_path):
        print(f"❌ Error: The file {psd_file_path} does not exist.")
        return

    psApp = win32com.client.Dispatch("Photoshop.Application")
    jpgSaveOptions = win32com.client.Dispatch("Photoshop.JPEGSaveOptions")
    jpgSaveOptions.EmbedColorProfile = True
    jpgSaveOptions.FormatOptions = 1
    jpgSaveOptions.Matte = 1
    jpgSaveOptions.Quality = 12

    current_dir = os.getcwd()
    try:
        psApp.Open(psd_file_path)
        doc = psApp.Application.ActiveDocument

        # Update vote data layers
        for layer in doc.Layers:
            if hasattr(layer, 'Kind') and layer.Kind == 2:  # Text layer
                if layer.Name in vote_data:
                    vote_value = vote_data[layer.Name]
                    if vote_value is None:
                        vote_value = 0
                    layer.TextItem.Contents = str(vote_value)

        # Update district name layer
        for layer in doc.Layers:
            if hasattr(layer, 'Kind') and layer.Kind == 2 and layer.Name == "district_name":
                layer.TextItem.Contents = district_name

        # Update general data layers (e.g., total votes, valid votes, etc.)
        for layer in doc.Layers:
            if hasattr(layer, 'Kind') and layer.Kind == 2:
                if layer.Name == "valid_votes":
                    valid_votes = general_data.get("valid", 0)
                    layer.TextItem.Contents = str(valid_votes)
                elif layer.Name == "total_votes":
                    total_votes = general_data.get("polled", 0)
                    layer.TextItem.Contents = str(total_votes)
                elif layer.Name == "registered_votes":
                    registered_votes = general_data.get("electors", 0)
                    layer.TextItem.Contents = str(registered_votes)
                elif layer.Name == "rejected_votes":
                    rejected_votes = general_data.get("rejected", 0)
                    layer.TextItem.Contents = str(rejected_votes)

        output_file_path = os.path.join(current_dir, f"{district_name}.jpg")
        doc.SaveAs(output_file_path, jpgSaveOptions, True)

        # Send the image to Discord after saving
        send_image_to_discord(output_file_path)

    except Exception as e:
        print(f"❌ Error processing image: {e}")

def send_image_to_discord(image_path):
    message = {
        "content": f"<@{user_id}> Here is the image you requested!"
    }

    files = {
        'file': open(image_path, 'rb')
    }

    try:
        response = requests.post(webhook_url, data=message, files=files)
        if response.status_code == 200:
            print("✅ Image sent successfully to Discord!")
        else:
            print(f"❌ Failed to send image to Discord: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending to Discord: {e}")
    finally:
        files['file'].close()

def monitor_website():
    last_links = {}
    translator = Translator()

    Tk().withdraw()
    current_dir = os.getcwd()
    psd_files = glob(os.path.join(current_dir, '*.psd'))
    psd_file_path = psd_files[0] if psd_files else askopenfilename(title="Select the PSD file", filetypes=[("PSD files", "*.psd")])

    if not psd_file_path:
        print("❌ No PSD file selected. Exiting.")
        return

    while True:
        try:
            current_data = fetch_website_data()
            if current_data:
                current_links = extract_division_links(current_data)
                new_divisions = {division: url for division, url in current_links.items() if division not in last_links}

                for division, url in new_divisions.items():
                    print(f"👉 Do you want to create an image for {division}? (y/n): ", end='', flush=True)
                    while True:
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key in ['y', 'n']:
                            create_image = key
                            print(key)
                            break
                    if create_image == 'n':
                        continue  # Skip to the next division

                    candidate_data, general_data = extract_division_results(url)

                    translated = translator.translate(division, src='en', dest='si')
                    sinhala_district_name = translated.text.replace("දිස්ත්රික්", "දිස්ත්‍රික්කය")

                    district_name = input(f"👉 Please enter the district name for {division}: ").strip()
                    # correct_translation = input(f"👉 Is the translated district name '{sinhala_district_name}' correct? (y/n): ").strip().lower()
                    # if correct_translation != 'y':
                    #     district_name = input("👉 Please enter the correct district name: ").strip()
                    # else:
                    #     district_name = sinhala_district_name

                    vote_data = {**candidate_data, "district_name": district_name}
                    process_json_to_image(psd_file_path, district_name, vote_data, general_data)

                last_links = current_links
            time.sleep(10)
        except Exception as e:
            print(f"[ERROR] Error in monitoring loop: {e}")

if __name__ == "__main__":
    monitor_website()
