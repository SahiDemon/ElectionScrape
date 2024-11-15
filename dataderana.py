import json
import requests
from discord_webhook import DiscordWebhook
from bs4 import BeautifulSoup
import time

# Configuration
website_url = "https://election.adaderana.lk/general-election-2024/index.php"
base_url = "https://election.adaderana.lk/general-election-2024/"
webhook_url = "https://discord.com/api/webhooks/1287034526006247546/TBMen9EyrkGGvKzlsGWELZCFAq0dU9VECk2tFDmZkQ8AIalg-xT7asVQvmKr0B_PZ4-7"
role_id = "1287032549733957695"

# Map of site names to JSON field names
party_map = {
    "NPPJathika Jana Balawegaya": "npp_votes",
    "SJBSamagi Jana Balawegaya": "sjb_votes",
    "NDFNew Democratic Front": "ndf_votes",
    "UDVUnited Democratic Voice": "uvd_votes",
    "SLPPSri Lanka Podujana Peramuna": "slpp_votes",
    "MJPMinority Justice Party": "mjp_votes"
}

# Function to fetch website data
def fetch_website_data():
    try:
        print("[INFO] Fetching website data...")
        response = requests.get(website_url)
        response.raise_for_status()
        print("[INFO] Successfully fetched website data.")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request error: {e}")
        return None

# Function to extract division links
def extract_division_links(html):
    print("[INFO] Extracting division links...")
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    rows = soup.select("table.table tbody tr")
    for row in rows:
        division = row.find("td").text.strip()
        division_link = row.find("a", href=True)['href']
        full_url = base_url + division_link
        links[division] = full_url
    print(f"[INFO] Extracted {len(links)} division links.")
    return links

# Function to scrape division results
def extract_division_results(url):
    print(f"[INFO] Fetching results from URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidate_data = {json_key: None for json_key in party_map.values()}
    print("[INFO] Extracting candidate data...")

    # Using the CSS selector to locate results
    result_blocks = soup.select(".card-body > .district > .dis_ele_result > .dis_ele_result_block")
    print(f"[INFO] Found {len(result_blocks)} result blocks.")
    
    for result in result_blocks:
        try:
            result_text = result.get_text(separator="\n").strip()
            print(f"[DEBUG] Extracted Text: {result_text}")
            
            lines = result_text.split("\n")
            if len(lines) >= 4:
                party_abbreviation = lines[0].strip()
                party_full_name = lines[1].strip()
                votes_text = lines[-1].strip()

                full_party_name = party_abbreviation + party_full_name
                print(f"[DEBUG] Full Party Name: {full_party_name}")
                print(f"[DEBUG] Votes Text: {votes_text}")

                if full_party_name in party_map:
                    votes = ''.join(c for c in votes_text if c.isdigit())
                    candidate_data[party_map[full_party_name]] = int(votes) if votes.isdigit() else None
                    print(f"[INFO] Mapped {full_party_name} to {party_map[full_party_name]} with votes: {votes}")
                else:
                    print(f"[WARNING] Party not found in party_map: {full_party_name}")
        except Exception as e:
            print(f"[ERROR] Error processing result block: {e}")

    # Extract general voting summary
    general_data = {}
    print("[INFO] Extracting general voting summary...")
    try:
        summary_table = soup.find("div", class_="total-votes-summery").find("table")
        for row in summary_table.find_all("tr"):
            label = row.find("th").text.strip().lower()
            votes = int(row.find_all("td")[0].text.replace(',', ''))
            general_data[label] = votes
            print(f"[DEBUG] General Data: {label} = {votes}")
    except Exception as e:
        print(f"[ERROR] Error extracting general voting summary: {e}")

    return candidate_data, general_data

# Function to send JSON data to Discord
def send_json_to_discord(division, candidate_data, general_data):
    results = {
        "npp_votes": candidate_data.get("npp_votes"),
        "sjb_votes": candidate_data.get("sjb_votes"),
        "ndf_votes": candidate_data.get("ndf_votes"),
        "uvd_votes": candidate_data.get("uvd_votes"),
        "slpp_votes": candidate_data.get("slpp_votes"),
        "mjp_votes": candidate_data.get("mjp_votes"),
        "valid_votes": general_data.get("valid"),
        "total_votes": general_data.get("polled"),
        "registered_votes": general_data.get("electors"),
        "rejected_votes": general_data.get("rejected"),
        "district_name": division
    }

    print(f"[INFO] JSON Results for {division}: {json.dumps(results, indent=4)}")

    json_file_path = f"{division}_results.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)

    message = f"<@&{role_id}> election results scraped from **adaderana.lk** **{division}**."

    with open(json_file_path, 'rb') as json_file:
        webhook = DiscordWebhook(url=webhook_url, content=message)
        webhook.add_file(file=json_file, filename=json_file_path)
        response = webhook.execute()

    if response.status_code == 200:
        print(f"[INFO] Results for {division} sent to Discord successfully.")
    else:
        print(f"[ERROR] Failed to send results to Discord. Status code: {response.status_code}, Response: {response.text}")

# Main monitoring function
def monitor_website():
    last_links = {}
    while True:
        try:
            current_data = fetch_website_data()
            if current_data:
                current_links = extract_division_links(current_data)
                new_divisions = {division: url for division, url in current_links.items() if division not in last_links}

                for division, url in new_divisions.items():
                    print(f"[INFO] New data found for {division}. Fetching details...")
                    candidate_data, general_data = extract_division_results(url)
                    send_json_to_discord(division, candidate_data, general_data)

                last_links = current_links
            time.sleep(20)
        except Exception as e:
            print(f"[ERROR] Error in monitoring loop: {e}")

# Run the monitoring script
monitor_website()
