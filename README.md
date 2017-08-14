# mempass

Password manager, which tries to be simple to use, simple to backup, and secure. It works with a combination of entropy, passphrase and a service-dependant word. Each password is done by combining these 3 to a hash.

## Security model

This app is not a commercial service. If you lose your entropy or forget your passphrase, you are screwed. There is no way to recover those.

Remember to back up your entropy string! Simply copy your ~/.mempass/settings.conf after the first run to usb stick or to cloud. A hacker has to know your passphrase and get the entropy string to get the passwords.

Because passwords are generated deterministically from entropy and passphrase, you don't need to sync passwords or store anything on the cloud. Just copy the entropy part to different devices.

## Installation

This requires Kivy to run. Install Kivy as described in the website (https://kivy.org/#download)

To run from command line, type:

    kivy main.py

Note that you have to install the requirements (Faker and pycrypto) to the kivy virtualenv:

    kivy -m pip install Faker pycrypto

User-friendly packages might come out later.

## Usage

Type in a passphrase and a service-related word (for example: facebook, gmail, etc). Click the buttons to generate different passwords, which are automatically copied to clipboard.

The password is automatically removed from clipboard 15 seconds later, if it is still there (doesn't seem to work on all platforms unfortunately).

![screenshot](https://raw.githubusercontent.com/kangasbros/mempass/master/mempass_screenshot.png "Press the various buttons to generate deterministic content.")

## How does it work?

Missing an app for your favourite platform? Well, it should be quite easy to develop, since the idea of the app is very simple.

Passwords are just formed with the following equation:

    password = hash (entropy + passphrase + word)

The default algorithm to use is SHA2-HMAC.

## Acknowledgments

Some ideas: https://news.ycombinator.com/item?id=13674890

Was developed in a hackathon to learn some kivy UI development
