import json
import requests
from discord_webhook import DiscordWebhook
import time
from bs4 import BeautifulSoup

website_url = "https://results.elections.gov.lk/allisland.php"
# Webhook URL from your Discord server
webhook_url = "https://discord.com/api/webhooks/1287034526006247546/TBMen9EyrkGGvKzlsGWELZCFAq0dU9VECk2tFDmZkQ8AIalg-xT7asVQvmKr0B_PZ4-7"
# Discord role ID you want to ping
role_id = "1287032549733957695"

# Function to fetch website data
def fetch_website_data():
    try:
        response = requests.get(website_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request error occurred: {e}")
        return None

# Function to extract the relevant data
def extract_relevant_data(html):
    soup = BeautifulSoup(html, "html.parser")
    
    title = soup.find("h4", class_="card-title card-title-dash").text.strip()
    
    # Updated candidates mapping
    candidates = {
        "Jathika Jana Balawegaya": "npp_votes",
        "Samagi Jana Balawegaya": "sjb_votes",
        "New Democratic Front": "ndf_votes",
        "Sri Lanka Podujana Peramuna": "slpp_votes",
        "United Democratic Voice": "uvd_votes",
        "Sarvajana Balaya": "mjp_votes"
    }

    candidate_data = {}
    rows = soup.find_all("tr")
    for row in rows:
        name_column = row.find("h6")
        if name_column and name_column.text.strip() in candidates:
            name = name_column.text.strip()
            votes = int(row.find_all("td", align="right")[0].text.strip().replace(',', ''))
            candidate_data[candidates[name]] = votes

    general_data = {}
    table = soup.find_all("table", class_="select-table")[-1]
    rows = table.find_all("tr")
    for row in rows:
        title_row = row.find("p").text.strip()
        values = row.find_all("td", align="right")
        if values:
            votes = values[0].text.strip().replace(',', '')
            general_data[title_row] = {"votes": int(votes)}

    return title, candidate_data, general_data

# Function to send JSON data as a downloadable file
def send_json_to_discord(district, candidate_data, general_data):
    results = {
        "npp_votes": candidate_data.get("npp_votes"),
        "sjb_votes": candidate_data.get("sjb_votes"),
        "ndf_votes": candidate_data.get("ndf_votes"),
        "uvd_votes": candidate_data.get("uvd_votes"),
        "slpp_votes": candidate_data.get("slpp_votes"),
        "mjp_votes": candidate_data.get("mjp_votes"),
        "valid_votes": general_data.get("Valid Votes", {}).get("votes"),
        "total_votes": general_data.get("Total Polled", {}).get("votes"),
        "registered_votes": general_data.get("Total Electors", {}).get("votes"),
        "rejected_votes": general_data.get("Rejected Votes", {}).get("votes"),
        "district_name": district
    }

    # Save results to a JSON file
    json_file_path = f"{district}_results.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)

    # Prepare the message
    message = f"<@&{role_id}> election results scraped from **results.elections.gov.lk**  **{district}**."
    
    # Send the message with the file
    with open(json_file_path, 'rb') as json_file:
        webhook = DiscordWebhook(url=webhook_url, content=message)
        webhook.add_file(file=json_file, filename=json_file_path)
        response = webhook.execute()

    if response.status_code == 200:
        print(f"Results for {district} sent to Discord successfully.")
    else:
        print(f"Failed to send results to Discord. Status code: {response.status_code}, Response: {response.text}")

# Main monitoring function
def monitor_website():
    last_data = None
    while True:
        try:
            current_data = fetch_website_data()

            if current_data and current_data != last_data:
                title, candidate_data, general_data = extract_relevant_data(current_data)
                send_json_to_discord(title, candidate_data, general_data)
                last_data = current_data

            time.sleep(20)

        except Exception as e:
            print(f"Error occurred in monitoring loop: {e}")

# Run the monitoring script
monitor_website()
