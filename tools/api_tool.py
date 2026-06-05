import requests

def call_api(url):

    response = requests.get(url)

    return response.json()