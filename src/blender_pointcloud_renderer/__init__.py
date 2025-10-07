"""
Blender Point Cloud Renderer

A Python library for rendering point cloud sequences as individual colored spheres
using Blender's powerful 3D rendering engine.
"""

from .point_cloud_renderer import PointCloudRenderer
from .camera_trajectory import CameraTrajectory
from .ply_processor import PLYProcessor

__version__ = "1.0.0"
__all__ = ["PointCloudRenderer", "CameraTrajectory", "PLYProcessor"]