"""
Camera trajectory management for point cloud rendering.
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class CameraTrajectory:
    """Manages different types of camera trajectories for point cloud rendering."""
    
    def __init__(self):
        """Initialize the camera trajectory manager."""
        self.logger = logging.getLogger(__name__)
        self.trajectory_type = None
        self.trajectory_params = {}
    
    def set_trajectory(self, trajectory_type: str, **kwargs) -> None:
        """
        Set the camera trajectory type and parameters.
        
        Args:
            trajectory_type: Type of trajectory ('linear', 'circular', 'custom')
            **kwargs: Trajectory-specific parameters
        """
        self.trajectory_type = trajectory_type
        
        if trajectory_type == "linear":
            self._setup_linear_trajectory(**kwargs)
        elif trajectory_type == "circular":
            self._setup_circular_trajectory(**kwargs)
        elif trajectory_type == "custom":
            self._setup_custom_trajectory(**kwargs)
        else:
            raise ValueError(f"Unknown trajectory type: {trajectory_type}")
    
    def _setup_linear_trajectory(self,
                               start_pos: Tuple[float, float, float] = (0, 0, 5),
                               end_pos: Tuple[float, float, float] = (5, 0, 5),
                               look_at: Optional[Tuple[float, float, float]] = None,
                               fixed_rotation: Optional[Tuple[float, float, float]] = None,
                               **kwargs) -> None:
        """Setup linear camera trajectory."""
        self.trajectory_params.update({
            'start_pos': start_pos,
            'end_pos': end_pos,
            'look_at': look_at,
            'fixed_rotation': fixed_rotation
        })
    
    def _setup_circular_trajectory(self,
                                 center: Tuple[float, float, float] = (0, 0, 0),
                                 radius: float = 5.0,
                                 height: float = 2.0,
                                 start_angle: float = 0.0,
                                 end_angle: float = 2 * math.pi,
                                 look_at: Optional[Tuple[float, float, float]] = None,
                                 **kwargs) -> None:
        """Setup circular camera trajectory."""
        self.trajectory_params.update({
            'center': center,
            'radius': radius,
            'height': height,
            'start_angle': start_angle,
            'end_angle': end_angle,
            'look_at': look_at or center
        })
    
    def _setup_custom_trajectory(self, keyframes: Optional[List[Dict[str, Any]]] = None, **kwargs) -> None:
        """Setup custom camera trajectory with keyframes."""
        if keyframes is None:
            keyframes = []
        
        self.trajectory_params.update({
            'keyframes': keyframes
        })
    
    def get_info(self) -> Dict[str, Any]:
        """Get trajectory information for script generation."""
        return {
            'type': self.trajectory_type,
            'parameters': self.trajectory_params
        }
    
    def euler_to_rotation_matrix(self, euler_angles: Tuple[float, float, float]) -> np.ndarray:
        """
        Convert Euler angles to a 3x3 rotation matrix.
        
        Args:
            euler_angles: (pitch, yaw, roll) in radians
            
        Returns:
            3x3 rotation matrix
        """
        pitch, yaw, roll = euler_angles
        
        # Create rotation matrices
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(pitch), -math.sin(pitch)],
            [0, math.sin(pitch), math.cos(pitch)]
        ])
        
        Ry = np.array([
            [math.cos(yaw), 0, math.sin(yaw)],
            [0, 1, 0],
            [-math.sin(yaw), 0, math.cos(yaw)]
        ])
        
        Rz = np.array([
            [math.cos(roll), -math.sin(roll), 0],
            [math.sin(roll), math.cos(roll), 0],
            [0, 0, 1]
        ])
        
        # Combine rotations: R = Rz * Ry * Rx
        return Rz @ Ry @ Rx