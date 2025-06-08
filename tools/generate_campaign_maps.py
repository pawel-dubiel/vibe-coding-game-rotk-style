#!/usr/bin/env python3
"""
Campaign Map Generator
Automatically generates multiple campaign maps based on predefined regions.
"""

import json
import os
import sys
import subprocess
import argparse
from pathlib import Path


def load_map_definitions(definitions_file: str = None) -> dict:
    """Load map definitions from JSON file"""
    if definitions_file is None:
        definitions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'map_definitions.json')
    
    try:
        with open(definitions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Map definitions file not found: {definitions_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing map definitions: {e}")
        return {}


def generate_map(map_def: dict, tile_generator_path: str, dry_run: bool = False) -> bool:
    """Generate a single map based on definition"""
    bounds = map_def['bounds']
    bounds_str = f"{bounds['west']},{bounds['south']},{bounds['east']},{bounds['north']}"
    
    # Build command
    cmd = [
        'python', tile_generator_path,
        '--hex-size-km', str(map_def['hex_size_km']),
        '--zoom', str(map_def['zoom'])
    ]
    
    # Add bounds - use equals sign to avoid negative number parsing issues
    cmd.extend([f'--bounds={bounds_str}'])
    
    print(f"\n🗺️  Generating: {map_def['name']}")
    print(f"   Bounds: {bounds_str}")
    print(f"   Hex size: {map_def['hex_size_km']}km")
    print(f"   Zoom level: {map_def['zoom']}")
    
    if dry_run:
        print(f"   Command: {' '.join(cmd)}")
        return True
    
    try:
        # Run the tile generator with real-time output
        # Use unbuffered output by setting PYTHONUNBUFFERED
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, bufsize=0, universal_newlines=True, env=env)
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            if line:
                # Indent the output to show it's from the subprocess
                print(f"   {line.strip()}", flush=True)
        
        # Wait for process to complete and check return code
        return_code = process.wait()
        
        if return_code == 0:
            print(f"✅ Successfully generated map for {map_def['name']}")
            return True
        else:
            print(f"❌ Failed to generate {map_def['name']} (exit code: {return_code})")
            return False
        
    except Exception as e:
        print(f"❌ Failed to generate {map_def['name']}")
        print(f"   Error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Tile generator not found: {tile_generator_path}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate multiple campaign maps from definitions')
    parser.add_argument('--definitions', '-d', 
                       help='Path to map definitions JSON file')
    parser.add_argument('--map', '-m', action='append',
                       help='Generate only specific map(s) by name (can be used multiple times)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available map definitions and exit')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show commands that would be run without executing them')
    parser.add_argument('--tile-generator', 
                       default=os.path.join(os.path.dirname(__file__), 'tile_terrain_generator.py'),
                       help='Path to tile_terrain_generator.py')
    
    args = parser.parse_args()
    
    # Load map definitions
    definitions_data = load_map_definitions(args.definitions)
    if not definitions_data:
        return 1
    
    map_definitions = definitions_data.get('map_definitions', [])
    if not map_definitions:
        print("❌ No map definitions found")
        return 1
    
    # List mode
    if args.list:
        print("📋 Available map definitions:")
        for i, map_def in enumerate(map_definitions, 1):
            bounds = map_def['bounds']
            print(f"   {i:2d}. {map_def['name']}")
            print(f"       {map_def['description']}")
            print(f"       Bounds: {bounds['west']}°W to {bounds['east']}°E, {bounds['south']}°S to {bounds['north']}°N")
            print(f"       Resolution: {map_def['hex_size_km']}km/hex, zoom {map_def['zoom']}")
            print()
        return 0
    
    # Filter maps if specific ones requested
    if args.map:
        filtered_maps = []
        for map_name in args.map:
            found = False
            for map_def in map_definitions:
                if map_def['name'].lower() == map_name.lower():
                    filtered_maps.append(map_def)
                    found = True
                    break
            if not found:
                print(f"⚠️  Map '{map_name}' not found in definitions")
        map_definitions = filtered_maps
    
    if not map_definitions:
        print("❌ No maps to generate")
        return 1
    
    # Check if tile generator exists
    if not os.path.exists(args.tile_generator):
        print(f"❌ Tile generator not found: {args.tile_generator}")
        return 1
    
    print(f"🚀 Generating {len(map_definitions)} map(s)...")
    if args.dry_run:
        print("   (Dry run mode - no actual generation)")
    
    # Generate maps
    success_count = 0
    total_count = len(map_definitions)
    
    for i, map_def in enumerate(map_definitions, 1):
        print(f"\n📍 Progress: {i}/{total_count}")
        
        if generate_map(map_def, args.tile_generator, args.dry_run):
            success_count += 1
        
        # Add a small delay between maps to be respectful to tile servers
        if not args.dry_run and i < total_count:
            import time
            print("   ⏳ Waiting 2 seconds before next map...")
            time.sleep(2)
    
    # Summary
    print(f"\n📊 Generation Summary:")
    print(f"   Total maps: {total_count}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {total_count - success_count}")
    
    if success_count == total_count:
        print("✅ All maps generated successfully!")
        return 0
    else:
        print("⚠️  Some maps failed to generate")
        return 1


if __name__ == "__main__":
    sys.exit(main())