"""
Utility Functions for Adaptive DDoS Mitigation System
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_results(results: list, output_dir: str, prefix: str = "results"):
    """
    Save results to JSON file with timestamp
    
    Args:
        results: List of result dictionaries
        output_dir: Output directory
        prefix: Filename prefix
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    return str(filepath)


def setup_custom_logger(name: str, 
                       log_file: str = None,
                       level: str = "INFO") -> logging.Logger:
    """
    Setup custom logger
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string
    
    Args:
        bytes_value: Bytes to format
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_rate(rate: float) -> str:
    """
    Format packet rate to human-readable string
    
    Args:
        rate: Packets per second
        
    Returns:
        Formatted string (e.g., "15.3K pps")
    """
    if rate < 1000:
        return f"{rate:.1f} pps"
    elif rate < 1000000:
        return f"{rate/1000:.1f}K pps"
    else:
        return f"{rate/1000000:.1f}M pps"


def calculate_statistics(values: list) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with mean, min, max, std
    """
    import numpy as np
    
    if not values:
        return {'mean': 0, 'min': 0, 'max': 0, 'std': 0}
    
    return {
        'mean': float(np.mean(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'std': float(np.std(values)),
        'median': float(np.median(values))
    }


class PerformanceTimer:
    """Context manager for timing code blocks"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        import time
        self.elapsed = time.time() - self.start_time
        print(f"{self.name} took {self.elapsed*1000:.2f} ms")
