import requests
import json
import os

class bngblaster(object):
    """ Simple BNG Blaster Controller Wrapper """

    def __init__(self, host, port=8001, test_instance="test"):
        self.base_url = "http://%s:%s/api/v1/instances/%s" % (host, port, test_instance)
        self.headers = {"content-type": "application/json" }
        self.config = {}

    def status(self) -> str:
        try:
            return requests.get(self.base_url).json()["status"]
        except:
            return "error"

    def create(self, config_file):
        with open(config_file, "r") as f:
            self.config = json.load(f)
        requests.put(self.base_url, headers=self.headers, data=json.dumps(self.config))

    def delete(self):
        requests.delete(self.base_url)

    def start(self, arguments={}):
        requests.post(self.base_url+"/_start", headers=self.headers, data=json.dumps(arguments))

    def stop(self):
        requests.post(self.base_url+"/_stop", headers=self.headers)

    def command(self, command, arguments=None):
        data = {"command": command}
        if isinstance(arguments, dict): 
            data["arguments"] = arguments
        return requests.post(self.base_url+"/_command", headers=self.headers, data=json.dumps(data)).json()

    def download(self, source_file):
        try:
            os.remove(source_file)
        except:
            pass
        os.system("wget %s/%s" % (self.base_url, source_file))


