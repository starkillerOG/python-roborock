import asyncio
import subprocess

from roborock.web_api import RoborockApiClient


class ReverseEngineerer:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    async def setup(self):
        web_api = RoborockApiClient(username=self.username)
        user_data = await web_api.pass_login(self.password)
        home_data = await web_api.get_home_data_v2(user_data)

        print()
        device_selection = ""
        for i, device in enumerate(home_data.devices):
            device_selection += f"{i}) {device.name}\n"
        selected_id = input("Which device would you like to work with? Please select the number.\n" + device_selection)

        device = home_data.devices[int(selected_id)]
        local_key = device.local_key
        print(f"Local key is: {local_key}")
        with open("key.txt", "w") as f:
            f.write(local_key)
        print("Running mitmproxy...")
        subprocess.run(["mitmweb", "--mode", "wireguard", "-s", "decode.py", "-q"])


re = ReverseEngineerer("conway220@gmail.com", "1h!M7yb29mX")
asyncio.run(re.setup())
