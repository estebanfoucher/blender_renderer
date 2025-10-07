"""
Main point cloud renderer class.
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from .ply_processor import PLYProcessor
from .camera_trajectory import CameraTrajectory
from .blender_script_generator import BlenderScriptGenerator


class PointCloudRenderer:
    """
    Main class for rendering point cloud sequences using Blender.
    
    This class orchestrates the entire rendering process, from loading PLY files
    to generating Blender scripts and executing them.
    """
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 blender_executable: Optional[str] = None,
                 log_level: str = "INFO"):
        """
        Initialize the point cloud renderer.
        
        Args:
            input_dir: Directory containing PLY files
            output_dir: Directory for rendered output
            blender_executable: Path to Blender executable (auto-detected if None)
            log_level: Logging level
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.log_level = log_level
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.ply_processor = PLYProcessor()
        self.camera_trajectory = CameraTrajectory()
        self.script_generator = BlenderScriptGenerator()
        
        # Find Blender executable
        self.blender_executable = self._find_blender(blender_executable)
        
        self.logger.info("PointCloudRenderer initialized")
        self.logger.info(f"Input directory: {self.input_dir}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"Blender executable: {self.blender_executable}")
    
    def _find_blender(self, blender_executable: Optional[str]) -> str:
        """Find Blender executable."""
        if blender_executable:
            if Path(blender_executable).exists():
                return str(blender_executable)
            else:
                raise FileNotFoundError(f"Blender executable not found: {blender_executable}")
        
        # Try common Blender locations
        common_paths = [
            "blender",
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
        ]
        
        for path in common_paths:
            if shutil.which(path) or Path(path).exists():
                self.logger.info(f"Found Blender executable: {path}")
                return path
        
        raise FileNotFoundError(
            "Blender executable not found. Please install Blender or specify the path."
        )
    
    def load_point_cloud_sequence(self) -> List[Dict[str, Any]]:
        """Load all PLY files from the input directory."""
        self.logger.info(f"Loading point cloud files from {self.input_dir}...")
        
        # Find all PLY files
        ply_files = sorted(self.input_dir.glob("*.ply"))
        
        if not ply_files:
            raise FileNotFoundError(f"No PLY files found in {self.input_dir}")
        
        self.logger.info(f"Found {len(ply_files)} PLY files")
        
        # Load point cloud data
        point_clouds = []
        for i, ply_file in enumerate(ply_files):
            print(f"Loading PLY files: {i+1}/{len(ply_files)}", end="\r")
            
            try:
                # Get basic info about the PLY file
                info = self.ply_processor.get_ply_info(ply_file)
                
                point_clouds.append({
                    'frame_number': i + 1,
                    'file_path': str(ply_file),
                    'data': info
                })
                
            except Exception as e:
                self.logger.error(f"Error loading {ply_file}: {e}")
                continue
        
        self.logger.info(f"Successfully loaded {len(point_clouds)} point clouds")
        return point_clouds
    
    def set_camera_trajectory(self, trajectory_type: str, **kwargs) -> None:
        """Set the camera trajectory."""
        self.camera_trajectory.set_trajectory(trajectory_type, **kwargs)
        self.logger.info(f"Camera trajectory set to: {trajectory_type}")
    
    def get_default_render_settings(self) -> Dict[str, Any]:
        """Get default render settings."""
        return {
            'resolution_x': 1920,
            'resolution_y': 1080,
            'frame_start': 1,
            'frame_end': 100,
            'fps': 24,
            'file_format': 'PNG',
            'color_mode': 'RGB',
            'color_depth': '8',
            'compression': 15,
            'point_size': 0.01,
            'material_type': 'emission',
            'background_color': (0.0, 0.0, 0.0, 1.0),
        }
    
    def render_sequence(self, 
                       point_clouds: Optional[List[Dict[str, Any]]] = None,
                       render_settings: Optional[Dict[str, Any]] = None,
                       background: bool = True) -> str:
        """
        Render the complete point cloud sequence.
        
        Args:
            point_clouds: Point cloud data (loaded automatically if None)
            render_settings: Render settings (defaults used if None)
            background: Whether to run Blender in background mode
            
        Returns:
            Path to output directory containing rendered frames
        """
        # Load point clouds if not provided
        if point_clouds is None:
            point_clouds = self.load_point_cloud_sequence()
        
        # Use default render settings if not provided
        if render_settings is None:
            render_settings = self.get_default_render_settings()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Blender script
        script_path = self.output_dir / "render_script.py"
        self.script_generator.generate_script(
            point_clouds=point_clouds,
            camera_trajectory=self.camera_trajectory,
            render_settings=render_settings,
            output_dir=self.output_dir,
            script_path=script_path
        )
        
        # Execute Blender script
        self.logger.info("Starting Blender rendering...")
        
        blender_cmd = [self.blender_executable]
        if background:
            blender_cmd.append("--background")
        
        blender_cmd.extend([
            "--python", str(script_path),
            "--"
        ])
        
        try:
            result = subprocess.run(
                blender_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.output_dir)
            )
            
            if result.returncode == 0:
                self.logger.info("Blender rendering completed successfully!")
            else:
                self.logger.error(f"Blender rendering failed: {result.stderr}")
                raise RuntimeError(f"Blender rendering failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error running Blender: {e}")
            raise
        
        return str(self.output_dir)