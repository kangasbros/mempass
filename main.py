import os
import json
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.settings import (Settings, SettingsWithSidebar,
                               SettingsWithSpinner,
                               SettingsWithTabbedPanel)
from kivy.properties import OptionProperty, ObjectProperty
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard

import hmac
import hashlib
import base64
import binascii
import struct
import time
import decimal
import datetime

from functools import partial
from kivy.clock import Clock

from faker import Faker
import faker

kivy.require('1.9.0')

from kivy.config import Config
Config.set('graphics', 'width', '300')
Config.set('graphics', 'height', '200')
Window.size = (300, 200)

HMAC_MSG = b"mempass"

home_path = os.path.expanduser('~')

CONFIG_DIR = home_path + "/.mempass"
CONFIG_FILE = home_path + "/.mempass/settings.conf"

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

class GeneratorWidget(BoxLayout):

    generated_input = ObjectProperty(None)
    passphrase = ObjectProperty(None)
    word = ObjectProperty(None)
    msg_label = ObjectProperty(None)
    dropdown_btn = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        self.load_config()
        super(GeneratorWidget, self).__init__(*args, **kwargs)
        self.dropdown_btn.text = self.config['algo']

    # configuration functions

    def load_config(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        if os.path.exists(CONFIG_FILE):
            f = open(CONFIG_FILE)
            self.config = json.loads(f.read())
            f.close()
        elif not hasattr(self, 'config'):
            self.config = {
                'algo': 'SHA2-HMAC',
            }
        # load wordlist
        f = open("bip39_wordlist_en.txt")
        self.wordlist = f.readlines()
        f.close()
        self.wordlist = [w.replace("\n", "") for w in self.wordlist]

    def save_config(self):
        f = open(CONFIG_FILE, 'w')
        f.write(json.dumps(self.config))
        f.close()

    def select_algo(self, algo):
        self.config['algo'] = algo
        self.dropdown_btn.text = self.config['algo']
        self.save_config()

    # copy functions

    def remove_from_clipboard(self, pw, dt):
        if Clipboard.paste() == pw:
            Clipboard.copy("")
            self.msg_label.text = "clipboard emptied %s" % time.asctime()
        print "blaa", Clipboard.paste(), dt, pw

    def copy_to_clipboard(self, pw):
        Clipboard.copy(pw)
        # remove automatically from clipboard 90 seconds later
        Clock.schedule_once(partial(self.remove_from_clipboard, pw), 90)

    # hash generators

    def generate_hash(self, extra_data=""):
        dig = None
        msg = str(self.passphrase.text) + str(self.word.text) + extra_data
        if self.config['algo'] == 'SHA2-HMAC':
            dig = hmac.new(msg, msg=HMAC_MSG, digestmod=hashlib.sha256).digest()
        elif self.config['algo'] == 'SHA1-HMAC':
            dig = hmac.new(msg, msg=HMAC_MSG, digestmod=hashlib.sha1).digest()
        elif self.config['algo'] == 'RIPEMD160-HMAC':
            dig = hmac.new(msg, msg=HMAC_MSG, digestmod=hashlib.new('ripemd160')).digest()
        elif self.config['algo'] == 'SHA1':
            dig = hashlib.sha1(msg).digest()
        elif self.config['algo'] == 'RIPEMD160':
            dig = hashlib.new('ripemd160').update(msg).digest()
        return dig

    def generate_hex(self):
        dig = self.generate_hash()
        s = binascii.hexlify(dig)
        return s

    def generate_hex_full(self):
        pw = self.generate_hex()
        self.generated_input.text = pw[:4] + "..."
        self.copy_to_clipboard(pw)
        self.msg_label.text = "hex (%d) copied to clipboard" % len(pw)

    def generate_hex_half(self):
        pw = self.generate_hex()
        pw = pw[:(len(pw)/2)]
        self.generated_input.text = pw[:4] + "..."
        self.copy_to_clipboard(pw)
        self.msg_label.text = "hex half (%d) copied to clipboard" % len(pw)

    def generate_b64(self):
        dig = self.generate_hash()
        s = base64.b64encode(dig)
        return s

    def generate_b64_full(self):
        pw = self.generate_b64()
        self.generated_input.text = pw[:4] + "..."
        self.copy_to_clipboard(pw)
        self.msg_label.text = "b64 (%d) copied to clipboard" % len(pw)

    def generate_b64_half(self):
        pw = self.generate_b64()
        pw = pw[:(len(pw)/2)]
        self.generated_input.text = pw[:4] + "..."
        self.copy_to_clipboard(pw)
        self.msg_label.text = "b64 half (%d) copied to clipboard" % len(pw)

    # special generators

    def generate_profile(self):
        dig = self.generate_hash(extra_data="profile")
        fake = Faker()
        seed = int(dig[:8].encode('hex'), 16)
        fake.random.seed(seed)
        return fake.profile()

    def generate_username(self):
        profile = self.generate_profile()
        dig = self.generate_hash(extra_data="profile")
        random_looking_number = int(dig[:8].encode('hex'), 16)

        # check different data first
        realname = profile['name']
        username_type = random_looking_number % 8
        birthdate = datetime.datetime.strptime(profile['birthdate'], '%Y-%m-%d')
        parts = realname.split(" ")
        random_looking_word = self.wordlist[random_looking_number % len(self.wordlist)]

        # generate different usernames
        username = random_looking_word + str(random_looking_number % 100)
        if username_type == 0:
            username = parts[0].lower() + parts[1][:1].lower() + str(birthdate.year)[2:]
        elif username_type == 1:
            username = parts[1][:1].lower() + parts[0].lower() + str(birthdate.year)[2:]
        elif username_type == 3:
            username = parts[0].lower() + str(birthdate.year)[2:]
        elif username_type == 4:
            username = realname.replace(" ", ".").lower()
        elif username_type == 5:
            randword2 = self.wordlist[(random_looking_number * 2) % len(self.wordlist)]
            username = randword2[:4] + random_looking_word[:7]
        elif username_type == 6:
            randword2 = self.wordlist[(random_looking_number * 2) % len(self.wordlist)]
            username = randword2[:2] + random_looking_word[:3] + str(random_looking_number % 10)

        Clipboard.copy(username)
        self.msg_label.text = "username: %s" % username

    def generate_realname(self):
        name = self.generate_profile()['name']
        Clipboard.copy(name)
        self.msg_label.text = "realname: %s" % name

    def generate_address(self):
        address = self.generate_profile()['address']
        Clipboard.copy(address)
        self.msg_label.text = "realname: %s" % address

    def generate_profile_json(self):
        profile = self.generate_profile()
        Clipboard.copy(json.dumps(profile, cls=DecimalEncoder, sort_keys=True,
                indent=4, separators=(',', ': ')))
        self.msg_label.text = "profile json copied to clipboard"


class GenerateApp(App):

    def build(self):
        layout = GeneratorWidget()
        return layout

if __name__ == '__main__':
    GenerateApp().run()
