# Reverse Engineering
My hope with this guide is that contributing to this project becomes easier for those not familiar with reverse engineering.
To start, download this repository by cloning it or just downloading the zip in github.

## Pre-requisites
1) You'll need python on your system.
2) You need to download [mitm](https://mitmproxy.org/)
3) You need python-roborock accessible wherever you run this code
   ```bash
   pip install python-roborock
   ```
4) I have tested this with a iPhone, it will likely work on Android, but i cannot be 100% sure.
5) Your computer and phone should be on the same WiFi network as your vacuum
6) You need the WireGuard app on your phone.

## Getting Started.
1) Add your username and password to reverse_engineerer.py
2) Run the code
3) Select the device you want to work with
4) open the Wireguard app and scan the QR code that was opened in the web browser that opened after selecting your device.
5) Navigate to mitm.it on your phones browser and follow the instructions there to install the certificate.
6)
