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

kivy.require('1.9.0')

from kivy.config import Config
Config.set('graphics', 'width', '300')
Config.set('graphics', 'height', '200')
Window.size = (300, 200)

HMAC_MSG = b"mempass"

home_path = os.path.expanduser('~')

CONFIG_DIR = home_path + "/.mempass"
CONFIG_FILE = home_path + "/.mempass/settings.conf"

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
        Clipboard.copy(pw)
        self.msg_label.text = "hex (%d) copied to clipboard" % len(pw)

    def generate_hex_half(self):
        pw = self.generate_hex()
        pw = pw[:(len(pw)/2)]
        self.generated_input.text = pw[:4] + "..."
        Clipboard.copy(pw)
        self.msg_label.text = "hex half (%d) copied to clipboard" % len(pw)

    def generate_b64(self):
        dig = self.generate_hash()
        s = base64.b64encode(dig)
        return s

    def generate_b64_full(self):
        pw = self.generate_b64()
        self.generated_input.text = pw[:4] + "..."
        Clipboard.copy(pw)
        self.msg_label.text = "b64 (%d) copied to clipboard" % len(pw)

    def generate_b64_half(self):
        pw = self.generate_b64()
        pw = pw[:(len(pw)/2)]
        self.generated_input.text = pw[:4] + "..."
        Clipboard.copy(pw)
        self.msg_label.text = "b64 half (%d) copied to clipboard" % len(pw)

    # special generators

    def generate_username(self):
        dig = self.generate_hash(extra_data="username")
        first_number = int(dig[:4].encode('hex'), 16)
        second_number = int(dig[4:8].encode('hex'), 16)
        third_number = int(dig[8:12].encode('hex'), 16)
        word1 = self.wordlist[first_number % len(self.wordlist)]
        word2 = self.wordlist[second_number % len(self.wordlist)]
        username = word1[:6] + word2[:3] + str(third_number % 100)
        self.generated_input.text = username
        Clipboard.copy(username)
        self.msg_label.text = "username: %s" % username


class GenerateApp(App):

    def build(self):
        layout = GeneratorWidget()
        return layout

if __name__ == '__main__':
    GenerateApp().run()
