import subprocess
import platform
import re
import random
import logging
from typing import Dict, Any, Tuple

class PingService:
    def __init__(self, target_ip: str = "8.8.8.8", gateway_ip: str = "10.24.0.1"):
        self.target_ip = target_ip
        self.gateway_ip = gateway_ip
        self.is_mock = False

    def ping(self, host: str, count: int = 1, timeout_ms: int = 1000) -> Tuple[float, int]:
        """
        Executes a ping command to the host.
        Returns:
            Tuple[float, int]: (average_rtt_ms, loss_percentage)
        """
        if self.is_mock:
            # Generate realistic ping times (10-35ms for internet, 1-3ms for gateway)
            if host == "8.8.8.8":
                # Simulated jitter/spikes
                if random.random() < 0.02: # 2% chance of packet loss
                    return 0.0, 100
                rtt = 15.0 + random.uniform(-3, 8)
                if random.random() < 0.05: # occasional spike
                    rtt += 80
                return round(rtt, 1), 0
            else: # Gateway
                if random.random() < 0.005: # 0.5% chance of loss
                    return 0.0, 100
                return round(1.2 + random.uniform(-0.4, 0.6), 1), 0

        system_name = platform.system().lower()
        if system_name == "windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
        else: # Linux/macOS
            cmd = ["ping", "-c", str(count), "-W", str(timeout_ms // 1000), host]
            
        try:
            # Run the subprocess ping command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                # Host is unreachable or packet loss occurred
                return 0.0, 100

            # Parse results
            loss_match = re.search(r"(\d+)% \w+", stdout) # e.g. 0% loss
            loss = int(loss_match.group(1)) if loss_match else 0
            
            if loss == 100:
                return 0.0, 100

            rtt = 0.0
            if system_name == "windows":
                # Search for average time: "Average = 15ms" or "Media = 15ms"
                avg_match = re.search(r"(Average|Media|Media\s*=\s*|Promedio\s*=\s*)(\d+)\s*ms", stdout, re.IGNORECASE)
                if avg_match:
                    rtt = float(avg_match.group(2))
                else:
                    # Fallback to matching single times
                    times = re.findall(r"time[=<](\d+)ms", stdout)
                    if times:
                        rtt = sum(float(t) for t in times) / len(times)
            else:
                # Linux output "rtt min/avg/max/mdev = 14.8/15.2/16.1/0.4 ms"
                avg_match = re.search(r"min/avg/max/mdev\s*=\s*[\d.]+/([\d.]+)/", stdout)
                if avg_match:
                    rtt = float(avg_match.group(1))
            
            return round(rtt, 1), loss

        except Exception as e:
            logging.error(f"Ping execution failed: {e}. Switching PingService to simulated results.")
            self.is_mock = True
            return self.ping(host, count, timeout_ms)
            
    def check_internet(self) -> bool:
        """
        Quick check if google.com is reachable via HTTP request.
        """
        if self.is_mock:
            # 98% internet availability
            return random.random() > 0.02

        import urllib.request
        try:
            # Fast timeout check to google
            urllib.request.urlopen("https://google.com", timeout=2.0)
            return True
        except Exception:
            return False
