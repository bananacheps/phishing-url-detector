
import re
import math
from urllib.parse import urlparse


def extract_features(url):
    url = str(url)

    # Parse URL
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
    except Exception:
        domain = ""

    # 1. URL Length
    url_length = len(url)

    # 2. Domain Length
    domain_length = len(domain)

    # 3. Subdomain Count
    domain_clean = domain.split(":")[0]
    parts = domain_clean.split(".") if domain_clean else []

    if len(parts) > 2:
        subdomain_count = len(parts) - 2
    else:
        subdomain_count = 0

    # 4. Special Character Count
    special_char_count = len(
        re.findall(r"[^a-zA-Z0-9]", url)
    )

    # 5. Digit Count
    digit_count = len(
        re.findall(r"\d", url)
    )

    # 6. HTTPS Usage
    https_usage = (
        1 if url.lower().startswith("https://") else 0
    )

    # 7. URL Entropy
    if len(url) > 0:

        frequency = {}

        for char in url:
            frequency[char] = frequency.get(char, 0) + 1

        entropy = 0

        for count in frequency.values():

            probability = count / len(url)

            entropy -= (
                probability *
                math.log2(probability)
            )

    else:
        entropy = 0

    return [
        url_length,
        domain_length,
        subdomain_count,
        special_char_count,
        digit_count,
        https_usage,
        entropy
    ]
