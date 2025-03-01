"""Schema for the configuration file"""

FULL_SCHEMA = {
    "type": "object",
    "properties": {
        "environment": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "scheduling_mode": {"enum": ["LOCK", "SCHEDULER", "POLLING", "NONE"]},
                "lock_file": {"type": "string"},
                "connectivity": {
                    "type": "object",
                    "properties": {
  	                "connector": {"enum": ["NO_LINK", "HTTPS", "RIGETTI", "GRPC"]},
                        "mode": {"enum": ["REAL", "EMULATED", "RANDOM"]},
                        "qpu_ip_address": {"type": "string", "format": "hostname"},
                        "qpu_port": {"type": "number"},
                    },
                    "required": ["mode"],
                },
                "timeouts": {
                    "type": "object",
                    "properties": {
                        "http": {"type": "number"},
                        "lock": {"type": "number"},
                    },
                },
            },
            "required": ["scheduling_mode", "connectivity"],
            "jobs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "qubit": {"type": "array", "minItems": 1, "maxItems": 2},
                        "shots": {"type": "array", "minItems": 1, "maxItems": 2},
                        "walltime": {"type": "number"},
                    },
                },
            },
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "user": {"type": "string"},
                        "weight": {"type": "number", "minimum": 0, "maximum": 1},
                        "computations": {"type": "object"},
                    },
                    "required": ["user", "weight"],
                },
                "allOf": [
                    {
                        "$comment": "Validate that the sum of all user weights equals 1",
                        "allOf": [
                            {
                                "if": {"minItems": 1},
                                "then": {"$template": "totalWeightValidator"},
                            }
                        ],
                    }
                ],
            },
        },
    },
    "required": ["environment", "jobs", "users"],
}

# Implementation of the custom validator using JSON Schema extensions
# This would typically be implemented in your validation framework


def validate_total_weight(instance):
    """
    Custom validator to ensure the sum of all user weights equals 1.

    Args:
        instance: The "users" array to validate

    Returns:
        (bool, str): A tuple containing (is_valid, error_message)
    """
    if not instance or not isinstance(instance, list):
        return False, "Users must be a non-empty array"

    total_weight = sum(user.get("weight", 0) for user in instance)

    # Allow for small floating-point errors
    if abs(total_weight - 1.0) > 1e-10:
        return False, f"Sum of user weights must equal 1.0, but got {total_weight}"

    return True, ""

