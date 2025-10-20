import json
from ddl.modules.utility.resource_path import resource_path

_DEFAULTS = {
    "application": {
    "name": "DDL-MISSION CONTROL ",
        "settings": {
            "command_prefix": "/",
            "logs_folder": "./saves",
            "on_start_maximized": True,
            "on_start_port_update": True,
            "team_id": "1043"
        }
    },
    "version": { "version": "0.0.1", "status": "BETA" },
    "connection": {
        "alarm": True,
        "filter_character": "",
        "time_out": 2,
        "bauds_default": "115200",
        "bauds_dic": { "115200": 115200 }
    },
    "telemetry": {
        "rate_hz": 1,
        "csv": {
            "enable": True,
            "filename_pattern": "Flight_${TEAM_ID}.csv",
            "include_header": True,
            "header": [
                "TEAM_ID","MISSION_TIME","PACKET_COUNT","MODE","STATE","ALTITUDE",
                "TEMPERATURE","PRESSURE","VOLTAGE",
                "GYRO_R","GYRO_P","GYRO_Y",
                "ACCEL_R","ACCEL_P","ACCEL_Y",
                "MAG_R","MAG_P","MAG_Y",
                "AUTO_GYRO_ROTATION_RATE",
                "GPS_TIME","GPS_ALTITUDE","GPS_LATITUDE","GPS_LONGITUDE","GPS_SATS",
                "CMD_ECHO"
            ]
        }
    },
    "graphs": { "default_update_time": 1.0, "settings": { "antialias": True, "opengl": False, "cupy": True, "numba": True, "segmentedLineMode": "off" } },
    "simulation": { "enabled": True, "csv_profile_path": "./sim/pressure_profile.csv", "csv_column": "pressure_pa", "tx_interval_s": 1.0 }
}

class ConfigManager:
    _cache = {}

    @classmethod
    def _load(cls):
        if cls._cache:
            return cls._cache

        cfg = dict(_DEFAULTS)
        # try config.json
        try:
            with open(resource_path("config.json"), "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except FileNotFoundError:
            pass

        # try messages.json (merge shallowly)
        try:
            with open(resource_path("messages.json"), "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except FileNotFoundError:
            pass

        cls._cache = cfg
        return cls._cache

    @classmethod
    def get(cls, dotted_key, default=None):
        data = cls._load()
        cur = data
        for part in dotted_key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur
