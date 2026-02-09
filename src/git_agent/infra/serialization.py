import json
from dataclasses import asdict, is_dataclass


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)
