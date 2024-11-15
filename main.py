import os
import win32com.client
import json
from glob import glob
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from googletrans import Translator

def get_latest_json_file():
    downloads_path = os.path.join(os.environ['USERPROFILE'], 'Downloads')
    json_files = glob(os.path.join(downloads_path, '*.json'))
    if not json_files:
        return None
    latest_file = max(json_files, key=os.path.getctime)
    return latest_file

def process_json_file(json_file_path, psd_file_path, district_name, vote_data):
    if not os.path.exists(json_file_path):
        print(f"❌ Error: The file {json_file_path} does not exist.")
        return

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

    print("🔄 Processing the JSON file...")

    try:
        psApp.Open(psd_file_path)
        doc = psApp.Application.ActiveDocument

        for layer in doc.Layers:
            try:
                if hasattr(layer, 'Kind') and layer.Kind == 2:  
                    if layer.Name in vote_data:
                        vote_value = vote_data[layer.Name]
                        if vote_value is None:
                            vote_value = 0
                        layer.TextItem.Contents = str(vote_value)
            except Exception as e:
                print(f"⚠️ Error updating layer {layer.Name}: {e}")

        for layer in doc.Layers:
            try:
                if hasattr(layer, 'Kind') and layer.Kind == 2 and layer.Name == "district_name":
                    layer.TextItem.Contents = district_name
            except Exception as e:
                print(f"⚠️ Error updating district name layer: {e}")

        # Display specified vote details in descending order
        print("\nVote details (high to low):")
        specified_keys = ['npp_votes', 'sjb_votes', 'ndf_votes', 'uvd_votes', 'slpp_votes', 'mjp_votes']
        sorted_votes = sorted(((k, v if v is not None else 0) for k, v in vote_data.items() if k in specified_keys), key=lambda item: int(item[1]), reverse=True)
        for i, (key, value) in enumerate(sorted_votes, 1):
            print(f"{i}. {key}: {value}")

        confirm_save = input("\n🔄 Are you sure you want to save the file? Press 'y' to confirm: ").strip().lower()
        if confirm_save == 'y':
            output_file_path = os.path.join(current_dir, f"{district_name}.jpg")
            doc.SaveAs(output_file_path, jpgSaveOptions, True)
            print(f"✅ Saved: {output_file_path}")
        else:
            print("❌ Save operation cancelled.")
    except Exception as e:
        print(f"❌ Error processing the JSON file: {e}")

def main():
    try:
        print("Welcome to the Photoshop Batch Processor!")
        
        # Hide the root window
        Tk().withdraw()
        
        current_dir = os.getcwd()
        psd_files = glob(os.path.join(current_dir, '*.psd'))
        if psd_files:
            psd_file_path = psd_files[0]
            print(f"🔍 Found PSD file in current directory: {psd_file_path}")
        else:
            print("❌ No PSD file found in the current directory.")
            psd_file_path = askopenfilename(title="Select the Photoshop file (main.psd)", filetypes=[("PSD files", "*.psd")])
            if not psd_file_path:
                print("❌ No Photoshop file selected.")
                return

        translator = Translator()

        while True:
            latest_json_file = get_latest_json_file()
            if latest_json_file:
                use_latest = input(f"👉 Found latest JSON file: {latest_json_file}. Do you want to use this file? (y/n): ").strip().lower()
                if use_latest == 'y':
                    json_file_path = latest_json_file
                else:
                    print("👉 Please select the vote_data.json file.")
                    json_file_path = askopenfilename(title="Select the vote_data.json file", filetypes=[("JSON files", "*.json")])
                    if not json_file_path:
                        print("❌ No JSON file selected.")
                        continue
            else:
                print("👉 Please select the vote_data.json file.")
                json_file_path = askopenfilename(title="Select the vote_data.json file", filetypes=[("JSON files", "*.json")])
                if not json_file_path:
                    print("❌ No JSON file selected.")
                    continue

            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                vote_data = json.load(json_file)
                english_district_name = vote_data.get("district_name", "")
                translated = translator.translate(english_district_name, src='en', dest='si')
                sinhala_district_name = translated.text.replace("දිස්ත්රික්", "දිස්ත්‍රික්කය")
                print(f"🔄 Translated district name: {sinhala_district_name}")
                correct_translation = input(f"👉 Is this correct? (y/n): ").strip().lower()
                if correct_translation != 'y':
                    district_name = input("👉 Please enter the correct district name: ")
                else:
                    district_name = sinhala_district_name

            process_json_file(json_file_path, psd_file_path, district_name, vote_data)

            another_file = input("🔄 Do you want to process another JSON file? (yes/no): ").strip().lower()
            if another_file != 'yes':
                break

        print("🎉 Processing complete.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()