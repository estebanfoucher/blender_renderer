#!/usr/bin/env python3
"""
Working script to render the full video using the direct approach that works perfectly.
This uses the exact same logic as the successful test_direct_approach.py but for all frames.
"""

import bpy
import numpy as np
from mathutils import Vector, Euler
import math
import os
from pathlib import Path

# --- Configuration ---
INPUT_DIR = "full_video"
OUTPUT_DIR = "output/full_video_working/"

# Camera settings from dialog
CAMERA_POS = (5.4, -5, 3.5)
# convert to radians
CAMERA_ROT_DEGREES = (42, 90, 0)
CAMERA_ROT = (math.radians(CAMERA_ROT_DEGREES[0]), math.radians(CAMERA_ROT_DEGREES[1]), math.radians(CAMERA_ROT_DEGREES[2]))


# Render settings
RESOLUTION = (1920, 1080)
SPHERE_RADIUS = 0.01
N_SAMPLES = 1
STEP = 10

def load_ply_file(file_path):
    """
    Load PLY file and return data in the EXACT format used in sphere_optimized_script.py:
    - points: np.array with dtype=float64 (default numpy dtype)
    - colors: np.array with dtype=float64 (default numpy dtype) 
    - Colors normalized from [0,255] to [0,1] range
    """
    print(f"Loading PLY file: {file_path}")
    
    points = []
    colors = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the header end
    header_end = 0
    vertex_count = 0
    has_colors = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('element vertex'):
            vertex_count = int(line.split()[-1])
            print(f"Found {vertex_count} vertices")
        elif line.startswith('property uchar red'):
            has_colors = True
            print("Found color properties (uchar)")
        elif line == 'end_header':
            header_end = i + 1
            break
    
    print(f"Header ends at line {header_end}, has_colors: {has_colors}")
    
    # Parse vertex data
    for i in range(header_end, header_end + vertex_count):
        if i >= len(lines):
            break
            
        parts = lines[i].strip().split()
        if len(parts) >= 3:
            # Extract coordinates (float values)
            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            points.append([x, y, z])
            
            # Extract colors if available (uchar values 0-255)
            if has_colors and len(parts) >= 6:
                r, g, b = int(parts[3]), int(parts[4]), int(parts[5])
                # Normalize colors from [0, 255] to [0, 1] - EXACTLY like working script
                colors.append([r/255.0, g/255.0, b/255.0])
            elif has_colors:
                # Default color if missing
                colors.append([1.0, 1.0, 1.0])
    
    # Convert to numpy arrays with EXACT same dtype as working script (float64 default)
    points = np.array(points)  # Default dtype is float64
    colors = np.array(colors) if colors else None  # Default dtype is float64
    
    print(f"Loaded {len(points)} points, has_colors: {colors is not None}")
    print(f"Points dtype: {points.dtype}, Colors dtype: {colors.dtype if colors is not None else 'None'}")
    
    return points, colors

def clear_scene():
    """Clear the scene completely."""
    # Select and delete all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear all materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    # Clear all meshes
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    
    # Clear all collections
    for collection in bpy.data.collections:
        if collection.name != "Collection":  # Keep the default collection
            bpy.data.collections.remove(collection)
    
    print("✅ Scene cleared completely")

def setup_render_settings():
    """Setup render settings with black background (EXACT same as sphere_optimized_script.py)."""
    scene = bpy.context.scene
    
    # Set render engine to Cycles
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = N_SAMPLES
    
    # Set resolution
    scene.render.resolution_x = RESOLUTION[0]
    scene.render.resolution_y = RESOLUTION[1]
    
    # Set output format
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    
    # Set black background (EXACT same as working script)
    scene.world = bpy.data.worlds.new("BlackWorld")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.clear()
    
    # Add background shader
    bg_node = scene.world.node_tree.nodes.new(type='ShaderNodeBackground')
    bg_node.inputs['Color'].default_value = (0, 0, 0, 1)  # Black background
    bg_node.inputs['Strength'].default_value = 1.0
    
    # Add output node
    output_node = scene.world.node_tree.nodes.new(type='ShaderNodeOutputWorld')
    
    # Connect nodes
    scene.world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])

def setup_camera():
    """Setup camera."""
    # Create camera
    bpy.ops.object.camera_add(location=CAMERA_POS, align="WORLD")
    camera = bpy.context.object
    camera.name = "PointCloudCamera"
    
    # Set camera properties
    camera.data.type = 'PERSP'
    camera.data.angle = math.radians(50)
    
    # Set rotation
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = CAMERA_ROT
    
    # Make sure the camera is the active camera for rendering
    bpy.context.scene.camera = camera
    
    print(f"Camera created: {camera.name}")
    print(f"Camera position: {camera.location}")
    print(f"Camera rotation: {camera.rotation_euler}")
    
    return camera

def add_lighting():
    """Add lighting for sphere rendering (EXACT same as sphere_optimized_script.py)."""
    # Add sun light
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun_light = bpy.context.object
    sun_light.name = 'SunLight'
    sun_light.data.energy = 3.0
    sun_light.data.color = (1.0, 0.95, 0.8)  # Warm light
    
    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 10))
    area_light = bpy.context.object
    area_light.name = 'AreaLight'
    area_light.data.energy = 1000
    area_light.data.size = 5.0
    area_light.data.color = (0.8, 0.9, 1.0)  # Cool light

def create_sphere_material():
    """Create material for spheres."""
    material = bpy.data.materials.new(name="SphereMaterial")
    material.use_nodes = True
    
    # Clear default nodes
    material.node_tree.nodes.clear()
    
    # Add principled BSDF
    principled_node = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.inputs['Specular IOR Level'].default_value = 0.5
    principled_node.inputs['Roughness'].default_value = 0.3
    
    # Add output node
    output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    
    # Connect nodes
    material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    return material

def create_sphere_objects(points, colors=None):
    """Create individual sphere objects for each point (EXACT same as working direct approach)."""
    print(f"Creating {len(points)} sphere objects with radius {SPHERE_RADIUS}")
    
    # Create base sphere mesh
    bpy.ops.mesh.primitive_uv_sphere_add(radius=SPHERE_RADIUS, location=(0, 0, 0))
    base_sphere = bpy.context.object
    base_sphere.name = "BaseSphere"
    
    # Create material for spheres
    material = create_sphere_material()
    base_sphere.data.materials.append(material)
    
    # Create a collection for all spheres
    sphere_collection = bpy.data.collections.new("PointCloudSpheres")
    bpy.context.scene.collection.children.link(sphere_collection)
    
    # Create spheres for each point
    sphere_objects = []
    for i, point in enumerate(points):
        # Duplicate the base sphere
        sphere_obj = base_sphere.copy()
        sphere_obj.data = base_sphere.data.copy()
        sphere_obj.name = f"Sphere_{i:04d}"
        
        # Set position
        sphere_obj.location = point
        
        # Set color if available
        if colors is not None and i < len(colors):
            # Create a new material for this sphere with the specific color
            sphere_material = material.copy()
            sphere_material.name = f"SphereMaterial_{i:04d}"
            
            # Normalize color to [0, 1] if needed
            color = colors[i]
            if color.max() > 1.0:
                color = color / 255.0
            
            # Set the base color
            principled_node = sphere_material.node_tree.nodes.get('Principled BSDF')
            if principled_node:
                principled_node.inputs['Base Color'].default_value = (*color, 1.0)
            
            # Assign material
            sphere_obj.data.materials.clear()
            sphere_obj.data.materials.append(sphere_material)
        
        # Link to collection
        sphere_collection.objects.link(sphere_obj)
        sphere_objects.append(sphere_obj)
    
    # Remove the base sphere from the scene
    bpy.data.objects.remove(base_sphere, do_unlink=True)
    
    print(f"✅ Created {len(sphere_objects)} sphere objects with radius {SPHERE_RADIUS}")
    return sphere_objects

def main():
    """Main function to render all frames."""
    print("🚀 Starting full video rendering with working approach...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all PLY files
    input_path = Path(INPUT_DIR)
    ply_files = sorted(list(input_path.glob("*.ply")))
    total_frames = len(ply_files)
    
    print(f"📊 Found {total_frames} PLY files in {INPUT_DIR}")
    
    if total_frames == 0:
        print(f"❌ No PLY files found in {INPUT_DIR}")
        return
    
    # Clear the scene completely at the start
    clear_scene()
    
    # Setup render settings (including black background)
    setup_render_settings()
    
    # Setup camera
    camera = setup_camera()
    
    # Add lighting
    add_lighting()
    
    # Render each frame
    for i, ply_file in enumerate(ply_files):
        if i % STEP != 0:
            continue
        
        frame_number = i + 1
        print(f"\n🎬 Rendering frame {frame_number}/{total_frames}: {ply_file.name}")
        
        # Load PLY data
        points, colors = load_ply_file(str(ply_file))
        
        if points is None or len(points) == 0:
            print(f"❌ Error: No points loaded from {ply_file}")
            continue
        
        # Clear previous spheres only (keep camera and lights)
        for collection in bpy.data.collections:
            if collection.name.startswith("PointCloudSpheres"):
                bpy.data.collections.remove(collection)
        
        # Clear only sphere objects, not camera and lights
        for obj in bpy.data.objects:
            if obj.name.startswith("Sphere_"):
                bpy.data.objects.remove(obj, do_unlink=True)
        
        # Create sphere objects
        create_sphere_objects(points, colors)
        
        # Set output path for rendering
        output_file = os.path.join(OUTPUT_DIR, f"frame_{frame_number:04d}")
        bpy.context.scene.render.filepath = output_file
        
        # Render the scene
        print(f"🎬 Rendering frame {frame_number}...")
        bpy.ops.render.render(write_still=True)
        
        print(f"✅ Rendered frame {frame_number} to {output_file}.png")
    
    print(f"\n🎉 Full video rendering completed!")
    print(f"📂 Output saved to: {OUTPUT_DIR}")
    print(f"🎬 Rendered {total_frames} frames as colored spheres")
    
    # Show final statistics
    output_files = list(Path(OUTPUT_DIR).glob("*.png"))
    if output_files:
        total_size = sum(f.stat().st_size for f in output_files)
        avg_size = total_size / len(output_files)
        print(f"📊 Generated {len(output_files)} PNG files")
        print(f"📊 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📊 Average file size: {avg_size:,} bytes ({avg_size/1024:.1f} KB)")

if __name__ == "__main__":
    main()
