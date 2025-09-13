import re
from typing import Optional


def validate_phone_number(phone_number: str) -> bool:
    e164_pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(e164_pattern, phone_number))


def validate_twiml_url(url: str) -> bool:
    url_pattern = r'^https?://[^\s]+$'
    return bool(re.match(url_pattern, url))


def format_phone_number(phone_number: str, country_code: str = "+1") -> Optional[str]:
    digits_only = re.sub(r'\D', '', phone_number)
    
    if phone_number.startswith("+"):
        return phone_number if validate_phone_number(phone_number) else None
    
    if len(digits_only) == 10:
        formatted = f"{country_code}{digits_only}"
        return formatted if validate_phone_number(formatted) else None
    
    if len(digits_only) == 11 and digits_only.startswith("1"):
        formatted = f"+{digits_only}"
        return formatted if validate_phone_number(formatted) else None
    
    return None