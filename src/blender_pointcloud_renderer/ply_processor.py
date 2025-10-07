"""
PLY file processor for loading and validating point cloud data.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from plyfile import PlyData


class PLYProcessor:
    """Handles loading and processing of PLY point cloud files."""
    
    def __init__(self):
        """Initialize the PLY processor."""
        self.logger = logging.getLogger(__name__)
    
    def load_ply(self, file_path: Path) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Load a PLY file and return points and colors.
        
        Args:
            file_path: Path to the PLY file
            
        Returns:
            Tuple of (points, colors) arrays, or (None, None) if loading fails
        """
        try:
            plydata = PlyData.read(str(file_path))
            vertices = plydata['vertex']
            
            # Extract points
            points = np.column_stack([
                vertices['x'],
                vertices['y'], 
                vertices['z']
            ])
            
            # Extract colors if available
            colors = None
            property_names = [prop.name for prop in vertices.properties]
            if 'red' in property_names and 'green' in property_names and 'blue' in property_names:
                colors = np.column_stack([
                    vertices['red'],
                    vertices['green'],
                    vertices['blue']
                ])
                # Normalize colors to [0, 1] range if they're in [0, 255]
                if colors.max() > 1.0:
                    colors = colors.astype(np.float32) / 255.0
            
            return points, colors
            
        except Exception as e:
            self.logger.error(f"Error loading PLY file {file_path}: {e}")
            return None, None
    
    def get_ply_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about a PLY file without loading all data.
        
        Args:
            file_path: Path to the PLY file
            
        Returns:
            Dictionary containing file information
        """
        try:
            plydata = PlyData.read(str(file_path))
            vertices = plydata['vertex']
            
            # Get property names
            property_names = [prop.name for prop in vertices.properties]
            
            # Calculate bounds
            x_coords = vertices['x']
            y_coords = vertices['y']
            z_coords = vertices['z']
            
            bounds = {
                'min_x': float(x_coords.min()),
                'max_x': float(x_coords.max()),
                'min_y': float(y_coords.min()),
                'max_y': float(y_coords.max()),
                'min_z': float(z_coords.min()),
                'max_z': float(z_coords.max()),
                'center_x': float(x_coords.mean()),
                'center_y': float(y_coords.mean()),
                'center_z': float(z_coords.mean()),
            }
            
            info = {
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'point_count': len(vertices),
                'has_colors': 'red' in property_names and 'green' in property_names and 'blue' in property_names,
                'has_alpha': 'alpha' in property_names,
                'properties': property_names,
                'bounds': bounds
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting PLY info for {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'file_size': 0,
                'point_count': 0,
                'has_colors': False,
                'has_alpha': False,
                'properties': [],
                'bounds': {}
            }