import os
import io
import json
import pycurl
from time import sleep
from threading import Thread
from datetime import datetime
from colorama import init, Fore


class TwitterTurbo:
    MAIN = f"[{Fore.MAGENTA}Main{Fore.RESET}]"
    TURBO = f"[{Fore.GREEN}Turbo{Fore.RESET}]"
    INFO = f"[{Fore.GREEN}Info{Fore.RESET}]"
    INPUT = f"[{Fore.MAGENTA}Input{Fore.RESET}]"

    def __init__(self):
        self.attempts = 0
        self.ratelimits = 0
        self.requestspersec = 0

        self.username = ""
        self.username_claimed = False
        self.auth_tokens = self.load_tokens('./tokens.txt')

    @staticmethod
    def load_tokens(filepath):
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if 5 < len(line.strip()) < 32]

    def make_request(self, curl, url, headers, data=None):
        buffer = io.BytesIO()
        curl.setopt(pycurl.URL, url.encode('utf-8'))
        curl.setopt(pycurl.HTTPHEADER, [header.encode('utf-8') for header in headers])
        curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
        curl.setopt(pycurl.NOSIGNAL, 1)

        if data:
            curl.setopt(pycurl.POST, 1)
            curl.setopt(pycurl.POSTFIELDS, data.encode('utf-8'))

        curl.perform()
        return buffer.getvalue().decode('utf-8')

    def check_username(self):
        curl = pycurl.Curl()
        while not self.username_claimed:
            try:
                response = self.make_request(curl, f"https://api.twitter.com/i/users/username_available.json?username={self.username}", ["Authorization: Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"])
                json_response = json.loads(response)
                
                if 'valid' in json_response and json_response['valid']:
                    if self.claim_username(curl):
                        self.username_claimed = True
                        break
                elif 'errors' in json_response and any('Rate limit' in error.get('message', '') for error in json_response['errors']):
                    self.ratelimits += 1
                else:
                    self.attempts += 1
            except Exception as e:
                self.attempts += 1
            sleep(0.15)
        
        curl.close()

    def claim_username(self, curl):
        try:
            response = self.make_request(curl, "https://api.twitter.com/1.1/account/settings.json", ["Authorization: Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69",
            f"Cookie: auth_token={self.auth_tokens[0]};ct0=ebe026e8262ceda4b3e42586f8e5ff964dde2f81e168abe05ef20bc1f258a68ecead59c83db29427ee1a26ad6487b19e60bebf76ccf6f3c9fe57ea4089c288ed96b2e79a780b5f48b800c3f88fe5d638",
            "Referer: https://twitter.com/settings/screen_name",
            "X-CSRF-Token: ebe026e8262ceda4b3e42586f8e5ff964dde2f81e168abe05ef20bc1f258a68ecead59c83db29427ee1a26ad6487b19e60bebf76ccf6f3c9fe57ea4089c288ed96b2e79a780b5f48b800c3f88fe5d638"],
            f"screen_name={self.username}")
            return f'"screen_name":"{self.username}",' in response
        except Exception:
            return False

    def update_rps(self):
        while not self.username_claimed:
            before = self.attempts + self.ratelimits
            sleep(1)
            self.requestspersec = (self.attempts + self.ratelimits) - before

    def run(self):
        init()
        print(f"{self.MAIN} oWo Twitter Turbo\n")

        self.username = input(f'{self.INPUT} Target: ')
        threads = int(input(f'{self.INPUT} Threads: '))

        if len(self.username) < 5:
            print(f"\n{self.INFO} Invalid username format...")
            return

        pycurl.global_init(pycurl.GLOBAL_ALL)
        print(f'\n{self.INFO} All threads successfully initialised...\n')
        
        Thread(target=self.update_rps, daemon=True).start()
        
        for _ in range(threads):
            Thread(target=self.check_username, daemon=True).start()

        try:
            while not self.username_claimed:
                print(f"{self.TURBO} {self.attempts:,} attempts | RL: {self.ratelimits:,} | R/s: {self.requestspersec:,}", end="\r", flush=True)
                sleep(0.1)
            
            print(f"\n{self.INFO} Successfully claimed @{self.username} after {self.attempts + 1:,} attempts")
            print(f"{self.INFO} Time of claim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        except KeyboardInterrupt:
            print(f'\r{self.TURBO} Turbo stopped, after {self.attempts:,} attempts!\n', end="")
        finally:
            pycurl.global_cleanup()

if __name__ == "__main__":
    TwitterTurbo().run()
