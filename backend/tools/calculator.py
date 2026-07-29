import math
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "factorial": math.factorial,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": pow,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}

SAFE_NAMES = {
    "__builtins__": {},
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "factorial": math.factorial,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": pow,
}


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports +, -, *, /, %, **, //, parentheses, and functions like sqrt, sin, cos, tan, log, factorial. Constants: pi, e.

    Args:
        expression: The mathematical expression to evaluate, e.g. "2 + 3 * 4" or "sqrt(16) + sin(pi/2)"

    Returns:
        JSON string with the result.
    """
    try:
        sanitized = expression.strip()
        if not sanitized:
            return '{"success": false, "error": "Empty expression"}'

        disallowed = ["import", "exec", "eval", "open", "os.", "sys.", "__", "lambda", "class"]
        for word in disallowed:
            if word in sanitized.lower():
                return '{"success": false, "error": "Expression contains disallowed terms"}'

        result = eval(sanitized, {"__builtins__": {}}, SAFE_NAMES)

        if isinstance(result, float) and result == int(result) and abs(result) < 1e15:
            result = int(result)

        logger.info("Calculator: %s = %s", sanitized, result)
        return f'{{"success": true, "result": {result}}}'
    except ZeroDivisionError:
        return '{"success": false, "error": "Division by zero"}'
    except Exception as e:
        logger.error("Calculator error: %s", str(e))
        return f'{{"success": false, "error": "{str(e)}"}}'
