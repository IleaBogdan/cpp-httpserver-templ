#!/usr/bin/env python3
# generate_openapi.py

import os
import re
import sys
from pathlib import Path

def should_exclude_route(route_path):
    """Check if a route should be excluded from OpenAPI documentation."""
    exclude_patterns = [
        r'^/openapi\.yaml$',           # OpenAPI spec file
        r'^/static/swagger/',           # Swagger static files
        r'^/swagger/',                   # Swagger UI routes
        r'^/$',                           # Root route that redirects to Swagger
        r'^/static/<string>'
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, route_path):
            return True
    return False

def find_crow_routes(directory):
    """Scan all .cpp files in directory for Crow routes."""
    routes = []
    
    # Patterns to match different Crow route declarations
    patterns = [
        r'CROW_ROUTE\s*\(\s*[^,]+,\s*"([^"]+)"\s*\)',
        r'CROW_BLUEPRINT_ROUTE\s*\(\s*[^,]+,\s*[^,]+,\s*"([^"]+)"\s*\)',
    ]
    
    # HTTP method patterns
    method_pattern = r'\.methods\s*\(\s*"([^"]+)"_method\s*\)'
    
    for filepath in Path(directory).glob("*.cpp"):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Find all routes
            for pattern in patterns:
                for match in re.finditer(pattern, content):
                    route = match.group(1)
                    
                    # Skip excluded routes
                    if should_exclude_route(route):
                        print(f"Excluding route: {route}")
                        continue
                    
                    # Try to find the HTTP method
                    method_match = re.search(method_pattern, content[match.end():match.end()+200])
                    method = method_match.group(1).lower() if method_match else "get"
                    
                    routes.append({
                        'path': route,
                        'method': method,
                        'file': filepath.name
                    })
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
    
    return routes

def generate_openapi_yaml(routes, output_file="openapi.yaml"):
    """Generate OpenAPI YAML from found routes."""
    
    yaml_content = """openapi: 3.0.0
info:
  title: Crow API
  description: Auto-generated API documentation
  version: 1.0.0
servers:
  - url: http://localhost:1337
    description: Local server
paths:
"""
    
    for route in routes:
        path_entry = f"""  {route['path']}:
    {route['method']}:
      summary: {route['method'].upper()} {route['path']}
      description: Auto-generated endpoint from {route['file']}
      responses:
        '200':
          description: Successful response
"""
        yaml_content += path_entry
    
    yaml_content += """
components:
    schemas: {}
"""
    
    # Write the file
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"Generated {output_file} with {len(routes)} routes")

def main():
    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()
    
    # Output file path
    output_file = script_dir / "openapi.yaml"
    
    # Find all routes
    print("Scanning for Crow routes...")
    routes = find_crow_routes(script_dir)
    
    if not routes:
        print("No Crow routes found in .cpp files (excluding Swagger UI routes)")
        return
    
    # Generate YAML
    generate_openapi_yaml(routes, output_file)
    
    # Print found routes
    print("\nFound routes (excluding Swagger UI):")
    for route in routes:
        print(f"  {route['method'].upper():<6} {route['path']}")

if __name__ == "__main__":
    main()