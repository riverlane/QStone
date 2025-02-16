"""Schema for the configuration file"""

FULL_SCHEMA = {
    "type": "object",
    "properties": {
        "environment": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "qpu_ip_address": {"type": "string", "format": "hostname"},
                "qpu_port": {"type": "number"},
                "qpu_management": {"enum": ["LOCK", "SCHEDULER", "POLLING", "NONE"]},
                "job_count": {"type": "number"},
                "lock_file": {"type": "string"},
                "timeouts": {
                    "type": "object",
                    "properties": {
                        "http": {"type": "number"},
                        "lock": {"type": "number"},
                    },
                },
            },
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
                        "job_count": {"type": "number"},
                        "weight": {"type": "number"},
                        "computations": {"type": "object"},
                    },
                },
            },
        },
    },
}
