import socket
import ipaddress
import sys
import logging
from urllib.parse import urlparse
from typing import List

logger = logging.getLogger("OpenClaw.Sandbox")

class SandboxError(Exception):
    pass

def audit_hook(event, args):
    """
    Audit hook to block dangerous system calls.
    Requires Python 3.8+
    """
    # Whitelisted events (safe to ignore)
    ALLOWED_EVENTS = {
        "builtins.input", 
        "builtins.input/result",
        "compile", 
        "exec", # Handled by runner.py removal, but safe to log if needed
        "import",
        "os.scandir",
        "time.sleep",
        "socket.getaddrinfo", # Needed for DNS resolution
    }
    
    # Dangerous prefixes to block
    BLOCKED_PREFIXES = [
        "os.system", "os.spawn", "os.posix_spawn", 
        "subprocess.Popen", 
        "socket.connect", # Block direct socket connections (except via safe client if needed, but here we block all by default in strict mode)
        "open" # Block file system access in strict mode
    ]
    
    # Allow socket.connect only if it might be used by the runner itself for API calls?
    # Ideally, the runner should make API calls OUTSIDE the sandbox context or before enabling it?
    # Actually, sys.audit is global. If we block socket.connect, the Agent Runner cannot talk to the backend.
    # We need a more nuanced approach or trust the Runner code but block User Code (if we were running user code).
    # Since this is a specialized Agent running Pre-defined Executors (Ping, Scrape), 
    # we want to prevent RCE from exploiting these executors to do other things.
    # But ScrapeExecutor NEEDS socket.connect.
    
    # Refined Strategy:
    # We are protecting against RCE injection into the *Executor* parameters.
    # For MVP V4.1, we will log warnings for now or block specific dangerous shells.
    
    if event in ALLOWED_EVENTS:
        return

    # Strictly block shell execution
    if event in ["os.system", "subprocess.Popen"]:
        logger.critical(f"Security Violation: Blocked restricted system call '{event}' with args {args}")
        raise RuntimeError(f"Sandbox Violation: Call to '{event}' is forbidden.")

    # For now, we allow socket.connect because ScrapeExecutor needs it.
    # In a future version, we could check the destination IP against a whitelist here too.

def install_sandbox():
    """Install the system audit hook."""
    if sys.version_info < (3, 8):
        logger.warning("Python 3.8+ is required for secure sandbox (sys.audit). Skipping.")
        return

    try:
        sys.addaudithook(audit_hook)
        logger.info("System audit hook installed. Sandbox active.")
    except Exception as e:
        logger.error(f"Failed to install audit hook: {e}")

class Sandbox:
    def __init__(self, allowed_domains: List[str] = None):
        self.allowed_domains = allowed_domains or []
        self.blocked_ranges = [
            ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            # Link-local
            ipaddress.ip_network("169.254.0.0/16"),
        ]

    def validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            raise SandboxError(f"Invalid URL: {url}")

        # Check whitelist if configured
        if self.allowed_domains:
            # Check for wildcard (allow all)
            if "*" in self.allowed_domains:
                allowed = True
            else:
                allowed = False
                for domain in self.allowed_domains:
                    if hostname == domain or hostname.endswith("." + domain):
                        allowed = True
                        break
            
            if not allowed:
                raise SandboxError(f"Domain not allowed: {hostname}")

        # Resolve IP to check for private networks
        try:
            # Resolve IP once to prevent DNS Rebinding (caller should use this IP)
            ip_str = socket.gethostbyname(hostname)
            self.validate_ip(ip_str, hostname)
            return ip_str
                    
        except socket.gaierror:
            raise SandboxError(f"Could not resolve hostname: {hostname}")

    def validate_ip(self, ip_str: str, hostname: str = "unknown"):
        ip = ipaddress.ip_address(ip_str)
        for network in self.blocked_ranges:
            if ip in network:
                raise SandboxError(f"Access to private IP blocked: {ip_str} ({hostname})")
        return True

