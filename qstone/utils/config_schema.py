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
                "job_count": {"type": "number"},
                "qpu": {
                    "type": "object",
                    "properties": {
                        "mode": {"enum": ["REAL", "EMULATED", "RANDOM"]},
                    },
                    "required": ["mode"],
                },
                "connectivity": {
                    "type": "object",
                    "properties": {
                        "mode": {"enum": ["NO_LINK", "HTTPS", "RIGETTI", "GRPC"]},
                        "ip_address": {"type": "string", "format": "hostname"},
                        "qpu": {
                            "type": "object",
                            "properties": {
                                "port": {"type": "number"},
                                "ip_address": {"type": "string", "format": "hostname"},
                            },
                        },
                        "compiler": {
                            "type": "object",
                            "properties": {
                                "port": {"type": "number"},
                                "ip_address": {"type": "string", "format": "hostname"},
                            },
                        },
                        "target": {"type": "string"},
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
                        "app_args": {"type": "object"},
                        "app_logging_level": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 2,
                        },
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
                        "computations": {"type": "object"},
                    },
                    "required": ["user", "computation"],
                },
            },
        },
    },
    "required": ["environment", "jobs", "users"],
}
