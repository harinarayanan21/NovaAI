import json
import random
import string
import logging
import uuid
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def random_integer(min_val: int = 1, max_val: int = 100) -> str:
    """Generate a random integer within a range.

    Args:
        min_val: Minimum value (inclusive). Default 1.
        max_val: Maximum value (inclusive). Default 100.

    Returns:
        JSON with the random integer.
    """
    try:
        result = random.randint(min_val, max_val)
        logger.info("Random integer: %d (range %d-%d)", result, min_val, max_val)
        return json.dumps({"success": True, "result": result, "min": min_val, "max": max_val})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def random_password(length: int = 16, include_special: bool = True) -> str:
    """Generate a random secure password.

    Args:
        length: Password length. Default 16. Minimum 8.
        include_special: Include special characters. Default True.

    Returns:
        JSON with the generated password.
    """
    try:
        length = max(8, min(128, length))
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        password_chars = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
        ]
        if include_special:
            password_chars.append(random.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

        password_chars += [random.choice(chars) for _ in range(length - len(password_chars))]
        random.shuffle(password_chars)
        password = "".join(password_chars)

        logger.info("Generated password: length=%d", length)
        return json.dumps({"success": True, "password": password, "length": length})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def generate_otp(length: int = 6) -> str:
    """Generate a one-time password (OTP).

    Args:
        length: OTP digit count. Default 6. Range 4-10.

    Returns:
        JSON with the OTP.
    """
    try:
        length = max(4, min(10, length))
        otp = "".join([str(random.randint(0, 9)) for _ in range(length)])
        logger.info("Generated OTP: length=%d", length)
        return json.dumps({"success": True, "otp": otp, "length": length})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def generate_uuid() -> str:
    """Generate a random UUID (v4).

    Returns:
        JSON with the UUID string.
    """
    try:
        result = str(uuid.uuid4())
        logger.info("Generated UUID: %s", result)
        return json.dumps({"success": True, "uuid": result})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
