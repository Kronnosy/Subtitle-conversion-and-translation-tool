from consolemenu import ConsoleMenu, Screen
from consolemenu.items import FunctionItem, SubmenuItem
import re
import requests
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

api_key = None
target_language = "TR"

def save_api_key():
    global api_key
    api_key = input("Please enter your Deepl API key:")
    print("API key successfully registered.")

def set_target_language():
    global target_language
    target_language = input("Please enter the target language code (e.g. TR):")
    print("Target language successfully set.")

def show_current_settings():
    global api_key, target_language
    print(f"Current API Key: {api_key if api_key else 'Not set'}")
    print(f"Current Target Language: {target_language}")
    input("Press a key to continue...")

def convert_time_to_seconds(time_str):
    hours, minutes, seconds = map(float, time_str.replace(',', ':').split(':'))
    return hours * 3600 + minutes * 60 + seconds

def translate_time_to_seconds(time_str):
    parts = time_str.split(' --> ')
    start_time = parts[0].replace(',', ':')
    end_time = parts[1].replace(',', ':')

    start_seconds = sum(x * float(t) for x, t in zip([3600, 60, 1], start_time.split(':')))
    end_seconds = sum(x * float(t) for x, t in zip([3600, 60, 1], end_time.split(':')))

    return start_seconds, end_seconds

def ass_to_srt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        ass_data = f.read()

    dialogue_matches = re.findall(r'Dialogue: (\d+),(.*?),(.*?),(.*?),.*?,(.*?),.*?,.*?,.*?,(.*?)$', ass_data,
                                  re.MULTILINE)

    dialogue_matches = sorted(dialogue_matches, key=lambda x: convert_time_to_seconds(x[1]))

    srt_entries = []
    for index, match in enumerate(dialogue_matches, start=1):
        start_time = match[1].replace('.', ',')
        end_time = match[2].replace('.', ',')
        text = match[5]
        srt_entry = f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
        srt_entries.append(srt_entry)

    with open(output_file, 'w', encoding='utf-8') as srt_file:
        for entry in srt_entries:
            srt_file.write(entry)

    print(f"{input_file} has been successfully converted to {output_file}.")
    input("Press a key to continue...")

def translate_with_deepl(text, target_lang="TR"):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target_lang,
    }
    response = requests.post(url, data=params)
    translation = response.json()["translations"][0]["text"] if response.ok else None
    return translation

def translate_subtitle_chunk(chunk):
    timecode, text = chunk[1], ' '.join(chunk[2:])
    translated_text = translate_with_deepl(text, target_language)
    return f"{timecode}\n{translated_text}"

def translate_srt_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    lines = srt_content.split('\n\n')
    chunks = [line.strip().split('\n') for line in lines if len(line.strip()) > 0]

    total_chunks = len(chunks)
    translated_subtitles = []

    with tqdm(total=total_chunks, desc="Translating") as pbar, ThreadPoolExecutor() as executor:
        futures = [executor.submit(translate_subtitle_chunk, chunk) for chunk in chunks]

        for future in as_completed(futures):
            translated_subtitles.append(future.result())
            pbar.update(1)
            time.sleep(0.1) 

    translated_subtitles.sort(key=lambda x: translate_time_to_seconds(x.split("\n")[0]))  

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write('\n\n'.join(translated_subtitles))

    print(f"Translation completed successfully. The translated text was saved in {output_file}.")
    input("Press a key to continue...")

def ass_to_srt_handler():
    input_ass_file = input("Please enter the name of the .ass file:")
    output_srt_file = input("Please enter the name of the .srt file to be created:")
    ass_to_srt(input_ass_file, output_srt_file)

def translate_srt_handler():
    global api_key, target_language
    input_srt_file = input("Please enter the name of the SRT file you want to translate:")
    output_srt_file = input("Please enter the name of the file where you want to save the translated text:")
    translate_srt_file(input_srt_file, output_srt_file)

def main_menu():
    menu = ConsoleMenu("Subtitle conversion and translation tool",
                       '''
            _   __
           | | / /
           | |/ / _ __ ___  _ __  _ __   ___  ___ _   _
           |    \| '__/ _ \| '_ \| '_ \ / _ \/ __| | | |
           | |\  \ | | (_) | | | | | | | (_) \__ \ |_| |
           \_| \_/_|  \___/|_| |_|_| |_|\___/|___/\__, |
                                                   __/ |
                                                  |___/
                       ''')

    ass_to_srt_item = FunctionItem("Convert .ass to .srt", ass_to_srt_handler)
    translate_srt_item = FunctionItem("Translate SRT", translate_srt_handler)

    menu.append_item(ass_to_srt_item)
    menu.append_item(translate_srt_item)

    settings_menu = ConsoleMenu("Settings", "API key and target language settings")

    save_api_key_item = FunctionItem("Register API Key", save_api_key)
    set_target_language_item = FunctionItem("Set Target Language", set_target_language)
    show_settings_item = FunctionItem("Show Current Settings", show_current_settings)

    settings_menu.append_item(save_api_key_item)
    settings_menu.append_item(set_target_language_item)
    settings_menu.append_item(show_settings_item)
    
    menu.append_item(SubmenuItem("Settings", settings_menu, menu=menu))

    menu.show()

if __name__ == "__main__":
    main_menu()

