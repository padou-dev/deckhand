import http.client
import ssl
import time
import urllib.error
import urllib.request


def web_url(entry):
    scheme = entry.get("web_scheme", "http")
    return f"{scheme}://localhost:{entry['web_port']}"


def wait_until_ready(url, timeout=180, should_stop=None):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if should_stop and should_stop():
            return False
        try:
            urllib.request.urlopen(url, timeout=3, context=context)
            return True
        except urllib.error.HTTPError:
            return True
        except (OSError, http.client.HTTPException):
            time.sleep(2)
    return False