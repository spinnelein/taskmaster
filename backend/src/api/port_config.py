"""
Port configuration management for TaskMaster
NO EMOJIS
"""
import json
import os
from pathlib import Path

class PortConfig:
    """Manages port configuration shared between backend and frontend"""
    
    CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "port_config.json"
    DEFAULT_BACKEND_PORT = 8000
    DEFAULT_FRONTEND_PORT = 5173
    
    @classmethod
    def write_backend_port(cls, port: int):
        """Write the backend port to the shared config file"""
        config = cls._read_config()
        config['backend_port'] = port
        cls._write_config(config)
    
    @classmethod
    def write_frontend_port(cls, port: int):
        """Write the frontend port to the shared config file"""
        config = cls._read_config()
        config['frontend_port'] = port
        cls._write_config(config)
    
    @classmethod
    def get_backend_port(cls) -> int:
        """Get the backend port from config or return default"""
        config = cls._read_config()
        return config.get('backend_port', cls.DEFAULT_BACKEND_PORT)
    
    @classmethod
    def get_frontend_port(cls) -> int:
        """Get the frontend port from config or return default"""
        config = cls._read_config()
        return config.get('frontend_port', cls.DEFAULT_FRONTEND_PORT)
    
    @classmethod
    def _read_config(cls) -> dict:
        """Read the config file or return empty dict"""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @classmethod
    def _write_config(cls, config: dict):
        """Write config to file"""
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write port config: {e}")