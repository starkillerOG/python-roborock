import json

from roborock.protocol import MessageParser

LOCAL_KEY = "0geZKM8gZkySDz8O"

STORAGE = {"methods": {}}


def compare_dicts(dict1, dict2):
    changed_vars = {}
    # print(dict1)
    # print(dict2)
    try:
        IGNORE_KEYs = {"msg_seq", "id"}
        if isinstance(dict1, dict) and isinstance(dict2, dict):
            for key, value in dict1.items():
                if key not in IGNORE_KEYs:
                    if dict2.get(key) != value:
                        print(f"Status change: {key} changed to {dict2.get(key)}")
        else:
            if dict1 != dict2:
                print(f"{dict1} != {dict2}")
    except Exception:
        print(dict1)
        print(dict2)


def decode(message):
    global STORAGE
    parsed_message = MessageParser.parse(message, LOCAL_KEY)
    if parsed_message[0]:
        if parsed_message[0][0]:
            payload = parsed_message[0][0]
            if b"abc" in payload.payload:
                print("map")
                return "Map update"
            json_payload = json.loads(payload.payload.decode())
            print(json_payload)
            # print(json_payload)
            data_point_number, data_point = list(json_payload.get("dps").items())[0]
            method = payload.get_method()
            if isinstance(data_point, str):
                data_point_response = json.loads(data_point)

                params = data_point_response.get("params")
                result = data_point_response.get("result")
                dp_id = data_point_response.get("id")
            else:
                dp_id = None
                params = None
                result = None
            dumped_result = None
            if result is not None:
                dumped_result = json.dumps(result, indent=4)
            # print(result)
            dumped_result = f"Result: \n{dumped_result}\n" if dumped_result else ""
            final_response = (
                f"Protocol: {parsed_message[0][0].protocol}\n"
                f"Method: {method}\n"
                f"Params: {params}\n"
                f"{dumped_result}"
                f"DPS: {data_point_number}\n"
                f"ID:  {dp_id}\n"
            )
            response_dict = {
                "method": method,
                "params": params,
                "result": result,
                "dps": data_point_number,
                "id": dp_id,
            }
            # if method != "get_prop":
            #     print(response_dict)
            if dp_id not in STORAGE:
                STORAGE[dp_id] = {"outgoing": response_dict}
            else:
                STORAGE[dp_id]["incoming"] = response_dict
                method = STORAGE[dp_id]["outgoing"]["method"]
                if method != "get_prop" and method != "get_dynamic_map_diff":
                    print(STORAGE[dp_id])
                if method in STORAGE["methods"] and result != ["ok"]:
                    last_res = STORAGE["methods"][method]
                    # if result is not None and last_res is not None:
                        # changes = compare_dicts(last_res[0], result[0])
                    STORAGE["methods"][method] = result
                    # if changes:
                    #     print(changes)
                    # else:
                    #     print("No changes")
                    # print(last_res)
                    # print(result)
                if result != ["ok"]:
                    STORAGE["methods"][method] = result
                else:
                    print(result)
            return final_response
    return parsed_message


from mitmproxy import contentviews
from mitmproxy.addonmanager import Loader
from mitmproxy.contentviews import base, mqtt
from mitmproxy.utils import strutils


class RoborockControlPacket(mqtt.MQTTControlPacket):
    def __init__(self, packet):
        super().__init__(packet)

    def pprint(self):
        s = f"[{self.Names[self.packet_type]}]"
        if self.packet_type == self.PUBLISH:
            if not self.payload:
                return "Empty payload"
            topic_name = strutils.bytes_to_escaped_str(self.topic_name)
            payload = strutils.bytes_to_escaped_str(self.payload)
            try:
                payload = decode(self.payload)

            except Exception as ex:
                raise ex
            s += f" {payload} \n" f"Topic: '{topic_name}'"
            return s
        else:
            return super().pprint()


class Roborock(mqtt.ViewMQTT):
    name = "Roborock"

    def __call__(self, data, **metadata):
        mqtt_packet = RoborockControlPacket(data)
        text = mqtt_packet.pprint()
        return "Roborock", base.format_text(text)


view = Roborock()


def load(loader: Loader):
    contentviews.add(view)


def tcp_message(flow):
    message = flow.messages[-1]
    if b"rr/m/" in message.content:
        RoborockControlPacket(message.content).pprint()


def done():
    contentviews.remove(view)
