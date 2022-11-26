import requests

class HttpClient:
    def get(self, url, headers = None):
        # TODO: Add error handling
        return requests.get(url, headers=headers)

    def post(self, url, json = None, headers = None):
        # TODO: Add error handling
        print(url,json,headers)
        return requests.post(url, json = json, headers=headers)
