# mempass

Password manager, which tries to be simple to use, simple to backup, and secure. It works with a combination of entropy, passphrase and a service-dependant word. Each password is done by combining these 3 to a hash.

Note that this app is not a commercial service. If you lose your entropy or forget your passphrase, you are screwed. There is no way to recover those.

This requires Kivy to run. Install Kivy as described in the website (https://kivy.org/#download)

To run from command line, type:

    kivy main.py

Note that you have to install the requirements (only one is Faker) to the kivy virtualenv:

    kivy -m pip install Faker

User-friendly packages might come out later.

## Usage

Type in a passphrase and a service-related word. Click the buttons to generate different passwords, which are automatically copied to clipboard.

Remember to back up your entropy string! Simply copy your settings.conf after the first run to usb stick etc.

The password is automatically removed from clipboard 15 seconds later, if it is still there.

![screenshot](https://raw.githubusercontent.com/kangasbros/mempass/master/mempass_screenshot.png "Press the various buttons to generate deterministic content.")

## Acknowledgments

This project is inspired by: https://github.com/urbanski/SHA1_Pass

Was developed in a hackathon to learn some kivy UI development
