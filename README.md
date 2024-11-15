# Election Results Automation Tool

## Overview
This tool automates the extraction of election results, processes the data, and generates images that can be shared on Discord.

---

## Features
- **Web Scraping**: Extract division links and voting data from the election website.  
- **Image Generation**: Update Photoshop PSD templates with extracted data and save them as images.  
- **Discord Integration**: Automatically upload generated images to a Discord channel.  
- **Interactive Input**: User prompts for confirming or editing details.  

---

## Requirements
- **Libraries**: `requests`, `googletrans`, `beautifulsoup4`, `pywin32`, `tkinter`.  
- **Software**: Adobe Photoshop with scripting enabled.  
- **Configurations**: Update `webhook_url`, `user_id`, and `website_url` in the script.

---

## Setup
1. Install dependencies:
   ```bash
   pip install requests googletrans-python beautifulsoup4 pywin32
   ```
2. Ensure the PSD template is accessible.  
3. Run the script:
   ```bash
   python election_tool.py
   ```

---

## Workflow
1. Fetch and process data from the election results website.  
2. Update Photoshop template with extracted data.  
3. Save images and send them to Discord.  

---

## Notes
- Compatible with Windows and requires Photoshop.  
- PSD template layers must match expected data keys (e.g., `valid_votes`).  

--- 

Enjoy seamless election data visualization! 🚀
