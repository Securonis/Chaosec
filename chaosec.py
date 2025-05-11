#!/usr/bin/env python3
# chaosec.py - A traffic obfuscation tool for Securonis Linux

import argparse
import random
import socket
import threading
import time
import requests
import dns.resolver
import os
import sys
import signal
import logging
from typing import List, Dict, Any
from datetime import datetime
import ipaddress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('chaosec')

# Global flag to control threads
running = True

# Traffic patterns 
TRAFFIC_PATTERNS = {
    "browsing": {
        "http_ratio": 0.6,
        "dns_ratio": 0.3,
        "tcp_ratio": 0.1,
        "udp_ratio": 0.05,
        "interval_min": 1.0,
        "interval_max": 8.0
    },
    "streaming": {
        "http_ratio": 0.8,
        "dns_ratio": 0.1,
        "tcp_ratio": 0.05,
        "udp_ratio": 0.2,
        "interval_min": 0.5,
        "interval_max": 2.0
    },
    "gaming": {
        "http_ratio": 0.2,
        "dns_ratio": 0.1,
        "tcp_ratio": 0.3,
        "udp_ratio": 0.5,
        "interval_min": 0.1,
        "interval_max": 1.0
    },
    "chaotic": {
        "http_ratio": 1.0,
        "dns_ratio": 1.0,
        "tcp_ratio": 1.0,
        "udp_ratio": 1.0,
        "interval_min": 0.1,
        "interval_max": 0.5
    }
}

class ChaosecTool:
    def __init__(self):
        self.threads = []
        self.intensity = 1.0  # Default intensity multiplier
        self.pattern = "browsing"  # Default traffic pattern
        self.tor_mode = False  # If we're running under Tor (for patterns)
        self.stats = {"dns": 0, "http": 0, "tcp": 0, "udp": 0}
        
    def start(self, args):
        """Start noise generation based on provided arguments"""
        # Set intensity and pattern
        self.intensity = args.intensity
        self.pattern = args.pattern
        self.tor_mode = args.tor_mode
        
        # Show banner and startup info
        self._show_banner(args)
        
        # Start appropriate noise generators
        if args.dns_noise:
            thread = threading.Thread(target=self.generate_dns_noise)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            logger.info("DNS noise generator active")
            
        if args.http_flood:
            thread = threading.Thread(target=self.generate_http_noise)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            logger.info("HTTP traffic generator active")
            
        if args.tcp_noise:
            thread = threading.Thread(target=self.generate_tcp_noise)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            logger.info("TCP connection noise active")
            
        if args.udp_noise:
            thread = threading.Thread(target=self.generate_udp_noise)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            logger.info("UDP packet noise active")
            
        # Start statistics thread if verbose
        if args.verbose:
            thread = threading.Thread(target=self._print_stats)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        if not (args.dns_noise or args.http_flood or args.tcp_noise or args.udp_noise):
            logger.warning("No noise generators selected. Use --help for options.")
            return
            
        # Keep the main thread alive
        try:
            while running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def _show_banner(self, args):
        """Display the startup banner with information"""
        banner = """
        ██████╗██╗  ██╗ █████╗  ██████╗ ███████╗███████╗ ██████╗
       ██╔════╝██║  ██║██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝
       ██║     ███████║███████║██║   ██║███████╗█████╗  ██║     
       ██║     ██╔══██║██╔══██║██║   ██║╚════██║██╔══╝  ██║     
       ╚██████╗██║  ██║██║  ██║╚██████╔╝███████║███████╗╚██████╗
        ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝
        Traffic Obfuscation Tool for Securonis Linux
        """
        print(banner)
        
        # Show running configuration
        logger.info(f"Starting with pattern: {self.pattern}, intensity: {self.intensity}x")
        logger.info(f"Active modules: " + 
              ("DNS " if args.dns_noise else "") +
              ("HTTP " if args.http_flood else "") +
              ("TCP " if args.tcp_noise else "") +
              ("UDP " if args.udp_noise else ""))
        
        if self.tor_mode:
            logger.info("Tor mode: Active - Traffic will be optimized for Tor network")
        
    def _print_stats(self):
        """Print stats periodically if verbose mode is on"""
        while running:
            time.sleep(10)  # Update stats every 10 seconds
            logger.info(f"Traffic stats (last 10s): DNS:{self.stats['dns']} HTTP:{self.stats['http']} TCP:{self.stats['tcp']} UDP:{self.stats['udp']}")
            self.stats = {"dns": 0, "http": 0, "tcp": 0, "udp": 0}  # Reset counters
            
    def stop(self):
        """Stop all noise generation threads"""
        global running
        running = False
        logger.info("Stopping all noise generators...")
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=1.0)
        logger.info("Chaosec stopped successfully")
        
    def generate_dns_noise(self):
        """Generate random DNS queries to confuse traffic analysis"""
        domains = [
            "google.com", "facebook.com", "amazon.com", "github.com", 
            "wikipedia.org", "twitter.com", "instagram.com", "reddit.com",
            "netflix.com", "youtube.com", "twitch.tv", "apple.com",
            "microsoft.com", "yahoo.com", "cloudflare.com", "akamai.com",
            "gitlab.com", "medium.com", "spotify.com", "mozilla.org",
            "stackoverflow.com", "debian.org", "ubuntu.com", "archlinux.org",
            "linux.org", "kernel.org", "gnu.org", "python.org",
            "rust-lang.org", "golang.org", "nasa.gov"
        ]
        
        # Add random subdomains for more realism
        subdomains = ["www", "mail", "api", "blog", "shop", "store", "dev", "admin", 
                      "cdn", "img", "media", "video", "static", "app", "mobile", "m"]
        
        resolver = dns.resolver.Resolver()
        
        while running:
            try:
                # apply pattern and intensity
                if random.random() > TRAFFIC_PATTERNS[self.pattern]["dns_ratio"] * self.intensity:
                    time.sleep(0.1)
                    continue
                    
                # sometimes use a subdomain
                if random.random() > 0.5:
                    subdomain = random.choice(subdomains)
                    domain = f"{subdomain}.{random.choice(domains)}"
                else:
                    domain = random.choice(domains)
                    
                # mix up query types
                qtype = random.choice(['A', 'AAAA', 'MX', 'TXT', 'NS'])
                resolver.resolve(domain, qtype)
                
                # update stats
                self.stats["dns"] += 1
                
                # apply pattern-based timing
                sleep_time = random.uniform(
                    TRAFFIC_PATTERNS[self.pattern]["interval_min"],
                    TRAFFIC_PATTERNS[self.pattern]["interval_max"]
                ) / self.intensity
                
                # if in Tor mode, be more conservative with traffic bursts
                if self.tor_mode and sleep_time < 1.0:
                    sleep_time = max(sleep_time, 1.0)
                
                time.sleep(sleep_time)
            except Exception:
                # Just continue if DNS resolution fails
                pass
                
    def generate_http_noise(self):
        """Generate random HTTP requests to various safe sites"""
        urls = [
            "https://httpbin.org/get", "https://en.wikipedia.org/wiki/Special:Random",
            "https://www.eff.org", "https://www.torproject.org",
            "https://www.mozilla.org", "https://www.kernel.org",
            "https://www.debian.org", "https://www.ubuntu.com", 
            "https://www.archlinux.org", "https://www.python.org",
            "https://www.rust-lang.org", "https://www.gnu.org",
            "https://www.fsf.org", "https://www.linuxfoundation.org",
            "https://www.opensuse.org", "https://www.redhat.com",
            "https://www.kali.org", "https://www.gnome.org"
        ]
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        ]
        
        # Configure session
        session = requests.Session()
        
        while running:
            try:
                # apply pattern and intensity
                if random.random() > TRAFFIC_PATTERNS[self.pattern]["http_ratio"] * self.intensity:
                    time.sleep(0.1)
                    continue
                    
                url = random.choice(urls)
                headers = {"User-Agent": random.choice(user_agents)}
                
                # mix GET and POST requests
                if random.random() > 0.8:
                    # occasionally do a POST
                    data = {"timestamp": str(datetime.now()), "session": str(random.randint(1000, 9999))}
                    session.post(url, headers=headers, data=data, timeout=10)
                else:
                    # usually do a GET
                    session.get(url, headers=headers, timeout=10)
                
                # update stats
                self.stats["http"] += 1
                
                # apply pattern-based timing
                sleep_time = random.uniform(
                    TRAFFIC_PATTERNS[self.pattern]["interval_min"],
                    TRAFFIC_PATTERNS[self.pattern]["interval_max"]
                ) / self.intensity
                
                # if in Tor mode, be more conservative with traffic bursts
                if self.tor_mode and sleep_time < 1.0:
                    sleep_time = max(sleep_time, 1.0)
                
                time.sleep(sleep_time)
            except Exception:
                # Just continue if request fails
                pass
                
    def generate_tcp_noise(self):
        """Generate random TCP connections to confuse traffic analysis"""
        common_ports = [80, 443, 8080, 8443, 22, 25, 143, 993, 587, 110, 995]
        targets = [
            "mozilla.org", "kernel.org",
            "debian.org", "ubuntu.com", "archlinux.org", 
            "python.org", "rust-lang.org", "golang.org",
            "gnu.org", "fsf.org", "linuxfoundation.org",
            "opensuse.org", "redhat.com", "kali.org"
        ]
        
        # HTTP-like requests to make the traffic look more realistic
        http_requests = [
            b"GET / HTTP/1.1\r\nHost: {}\r\nUser-Agent: Mozilla/5.0\r\n\r\n",
            b"HEAD / HTTP/1.1\r\nHost: {}\r\nUser-Agent: Chrome/92.0\r\n\r\n",
            b"GET /index.html HTTP/1.1\r\nHost: {}\r\nUser-Agent: Firefox/89.0\r\n\r\n",
            b"GET /about HTTP/1.1\r\nHost: {}\r\nUser-Agent: Safari/605.1\r\n\r\n"
        ]
        
        while running:
            try:
                # apply pattern and intensity
                if random.random() > TRAFFIC_PATTERNS[self.pattern]["tcp_ratio"] * self.intensity:
                    time.sleep(0.1)
                    continue
                    
                target = random.choice(targets)
                port = random.choice(common_ports)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((target, port))
                
                # send a realistic-looking HTTP request if it's a common HTTP port
                if port in [80, 443, 8080, 8443]:
                    request = random.choice(http_requests)
                    sock.send(request.format(target.encode()))
                    
                    # sometimes read response
                    if random.random() > 0.7:
                        sock.recv(4096)
                
                sock.close()
                
                # update stats
                self.stats["tcp"] += 1
                
                # apply pattern-based timing
                sleep_time = random.uniform(
                    TRAFFIC_PATTERNS[self.pattern]["interval_min"],
                    TRAFFIC_PATTERNS[self.pattern]["interval_max"]
                ) / self.intensity
                
                # if in Tor mode, be more conservative with traffic bursts
                if self.tor_mode and sleep_time < 1.0:
                    sleep_time = max(sleep_time, 1.0)
                
                time.sleep(sleep_time)
            except Exception:
                # Just continue if connection fails
                pass
    
    def generate_udp_noise(self):
        """Generate random UDP packets to various destinations"""
        # Common UDP ports: DNS, NTP, SNMP, gaming ports, etc.
        common_ports = [53, 123, 161, 162, 1900, 5353, 27015, 3478, 3479]
        
        # Generate random IP addresses that aren't in private ranges
        def get_random_ip():
            while True:
                ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
                if not ipaddress.ip_address(ip).is_private:
                    return ip
        
        # Packet payloads for different protocols
        dns_payload = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07mozilla\x03org\x00\x00\x01\x00\x01"
        ntp_payload = b"\x1b" + b"\0" * 47  # NTP request mode 3
        
        while running:
            try:
                # apply pattern and intensity
                if random.random() > TRAFFIC_PATTERNS[self.pattern]["udp_ratio"] * self.intensity:
                    time.sleep(0.1)
                    continue
                
                # create a UDP socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                # choose port and prepare packet
                port = random.choice(common_ports)
                if port == 53:  # DNS
                    payload = dns_payload
                elif port == 123:  # NTP
                    payload = ntp_payload
                else:
                    # random data for other ports
                    payload = bytes(random.getrandbits(8) for _ in range(random.randint(16, 128)))
                
                # send to random IP or to known servers
                if random.random() > 0.5:
                    target_ip = get_random_ip()
                else:
                    target_ip = "8.8.8.8"  # Google DNS as an example
                
                sock.sendto(payload, (target_ip, port))
                sock.close()
                
                # update stats
                self.stats["udp"] += 1
                
                # apply pattern-based timing
                sleep_time = random.uniform(
                    TRAFFIC_PATTERNS[self.pattern]["interval_min"],
                    TRAFFIC_PATTERNS[self.pattern]["interval_max"]
                ) / self.intensity
                
                # if in Tor mode, be more conservative with traffic bursts
                if self.tor_mode and sleep_time < 1.0:
                    sleep_time = max(sleep_time, 1.0)
                
                time.sleep(sleep_time)
            except Exception:
                # Just continue if sending fails
                pass

def signal_handler(sig, frame):
    """Handle interrupt signals to gracefully stop the tool"""
    global running
    running = False
    logger.info("Interrupt received, shutting down...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Chaosec - Traffic obfuscation tool for Securonis Linux")
    
    # noise generators
    parser.add_argument("--dns-noise", action="store_true", help="Generate random DNS queries")
    parser.add_argument("--http-flood", action="store_true", help="Generate random HTTP requests")
    parser.add_argument("--tcp-noise", action="store_true", help="Generate random TCP connections")
    parser.add_argument("--udp-noise", action="store_true", help="Generate random UDP packets")
    
    # traffic pattern
    parser.add_argument("--pattern", choices=["browsing", "streaming", "gaming", "chaotic"], 
                      default="browsing", help="Traffic pattern to simulate")
    
    # intensity setting
    parser.add_argument("--intensity", type=float, default=1.0,
                      help="Traffic intensity multiplier (0.1-10.0)")
    
    # Tor mode - only affects traffic patterns, doesn't route through Tor
    parser.add_argument("--tor-mode", action="store_true", 
                      help="Optimize traffic patterns for Tor network")
    
    # Various options
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Enable verbose output with statistics")
    parser.add_argument("--mode", choices=["standard", "chaotic"], default="standard",
                      help="Legacy mode setting (use --pattern instead)")
    
    args = parser.parse_args()
    
    # input validation
    if args.intensity < 0.1 or args.intensity > 10.0:
        logger.error("Intensity must be between 0.1 and 10.0")
        sys.exit(1)
    
    # backward compatibility: map mode to pattern if specified
    if args.mode == "chaotic" and args.pattern == "browsing":
        args.pattern = "chaotic"
    
    # setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # start the tool
    tool = ChaosecTool()
    tool.start(args)

if __name__ == "__main__":
    main() 
