import os
import sys
import json
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
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

from Crypto.Cipher import AES

from functools import partial
from kivy.clock import Clock

from faker import Faker
import faker

kivy.require('1.9.0')

from kivy.config import Config
Config.set('graphics', 'width', '300')
Config.set('graphics', 'height', '170')
Window.size = (300, 170)

HMAC_MSG = b"mempass"

home_path = os.path.expanduser('~')

CONFIG_DIR = home_path + "/.mempass"
CONFIG_FILE = CONFIG_DIR + "/settings.conf"

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

    def generate_entropy_phrase(self):
        if "entropy" in self.config.keys():
            raise Exception("Can't generate entropy if entropy already exists!")
        self.config["entropy"] = base64.b64encode(os.urandom(16))
        entropy_backup_file = CONFIG_DIR + "/entropy_" + datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        f = open(entropy_backup_file, 'w')
        f.write(json.dumps(self.config))
        f.close()
        # self.msg_label.text = "Back up your entropy!"

    # configuration functions

    def load_config(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        if os.path.exists(CONFIG_FILE):
            f = open(CONFIG_FILE)
            self.config = json.loads(f.read())
            f.close()
            # you can define custom HMAC MSG in the config file
            if "HMAC_MSG" in self.config.keys():
                global HMAC_MSG
                HMAC_MSG = self.config["HMAC_MSG"]
        elif not hasattr(self, 'config'):
            self.config = {
                'algo': 'SHA2-HMAC',
            }
            self.generate_entropy_phrase()
            self.save_config()
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

    def copy_to_clipboard(self, pw):
        Clipboard.copy(pw)
        # remove automatically from clipboard 90 seconds later
        Clock.schedule_once(partial(self.remove_from_clipboard, pw), 15)

    # hash generators

    def generate_hash(self, extra_data=""):
        dig = None
        entropy = ""
        if "entropy" in self.config.keys():
            entropy = self.config["entropy"]
        msg = entropy + str(self.passphrase.text) + str(self.word.text) + extra_data
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
        randword2 = self.wordlist[(random_looking_number * 2) % len(self.wordlist)]

        # generate different usernames
        username = randword2[:3] + random_looking_word + str(random_looking_number % 100)

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

    # additional notes, local only

    def note_directory_name(self):
        return binascii.hexlify(self.generate_hash(extra_data="_notes_filename_dir"))[:2]

    def note_file_name(self, index):
        filepath_digest = self.generate_hash(extra_data="_notes_filename")
        return binascii.hexlify(filepath_digest)[:32] + "_" + str(index)

    def note_encryption_key(self, index):
        encryption_key_data = self.generate_hash(extra_data="_encryption_key_"+str(index))
        return encryption_key_data[:16]

    def note_IV456(self, index):
        IV456_data = self.generate_hash(extra_data="_IV456_"+str(index))
        return IV456_data[:16]

    def read_notes(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        notedir = self.note_directory_name()
        i = 0
        final_text = ""
        while True:
            filepath = CONFIG_DIR + "/" + notedir + "/" + self.note_file_name(i)
            if not os.path.exists(filepath):
                break
            else:
                f = open(filepath, 'r')
                cipher = AES.new(self.note_encryption_key(i), AES.MODE_CBC, self.note_IV456(i))
                decrypted = cipher.decrypt(f.read())
                final_text += decrypted.rstrip() + "\n"
            i += 1

        if not final_text:
            final_text = "no notes"

        # print final_text

        Builder.unload_file('kv/read_notes_popup.kv')
        # load the content of the .kv file
        content = Builder.load_file('kv/read_notes_popup.kv')
        content.note_text.text = final_text
        self.popup = Popup(title='Notes ' + notedir,
        content=content)
        #content.cancel_button.on_release = self.popup.dismiss
        #content.add_note_button.on_release = self.add_note
        self.popup.open()


    def add_note(self, content):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        notedir = self.note_directory_name()
        if not os.path.exists(CONFIG_DIR + "/" + notedir):
            os.makedirs(CONFIG_DIR + "/" + notedir)
        i = 0
        while True:
            filepath = CONFIG_DIR + "/" + notedir + "/" + self.note_file_name(i)
            if not os.path.exists(filepath):
                cipher = AES.new(self.note_encryption_key(i), AES.MODE_CBC, self.note_IV456(i))

                plaintext = (unicode(datetime.datetime.utcnow())+"\n"+content).encode('utf-8')
                l = len(plaintext)
                ciphertext = cipher.encrypt(plaintext + ((16 - l%16) * ' '))

                f = open(filepath, 'w')
                f.write(ciphertext)
                f.close()
                self.msg_label.text = "note added: " + filepath[:50] + "..."
                return
            i += 1

    def add_note_popup(self):
        # unload the content of the .kv file
        # reason: it could have data from previous calls
        Builder.unload_file('kv/add_note_popup.kv')
        # load the content of the .kv file
        content = Builder.load_file('kv/add_note_popup.kv')
        self.popup = Popup(title='Add note',
        content=content)
        #content.cancel_button.on_release = self.popup.dismiss
        #content.add_note_button.on_release = self.add_note
        self.popup.open()


class GenerateApp(App):

    def build(self):
        self.layout = GeneratorWidget()
        return self.layout

    def add_note(self, content):
        # print "blaa222", dir(self.layout.popup)
        print "blaa", content
        self.layout.add_note(content)
        self.layout.popup.dismiss()

    def close_popup(self):
        self.layout.popup.dismiss()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        custom_configuration = sys.argv[1]
        CONFIG_DIR = home_path + "/.mempass_" + custom_configuration
        CONFIG_FILE = CONFIG_DIR + "/settings.conf"
        print "CUSTOM CONFIGURATION:", custom_configuration, CONFIG_FILE
    GenerateApp().run()
