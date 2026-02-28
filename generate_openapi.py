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

def extract_parameters(route_content, route_path):
    """Extract query parameters and body parameters from route implementation."""
    params = {
        'query': [],
        'body': []
    }
    
    # Look for url_params.get() calls which indicate query parameters
    query_pattern = r'url_params\.get\s*\(\s*["\']([^"\']+)["\']\s*\)'
    query_matches = re.finditer(query_pattern, route_content)
    for match in query_matches:
        param_name = match.group(1)
        if param_name not in params['query']:
            params['query'].append(param_name)
    
    # Look for JSON body parsing patterns
    body_patterns = [
        # Pattern for crow::json::load
        r'crow::json::load\s*\(\s*req\.body\s*\)',
        # Pattern for accessing JSON properties
        r'body_json\[\s*["\']([^"\']+)["\']\s*\]',
        r'body\[\s*["\']([^"\']+)["\']\s*\]',
        # Pattern for .s() calls on JSON values
        r'\[\s*["\']([^"\']+)["\']\s*\]\s*\.s\s*\(\s*\)',
        # Pattern for crow::json::rvalue access
        r'body\[["\']([^"\']+)["\']\]',
    ]
    
    # First check if this route handles JSON body
    has_json_body = False
    for pattern in body_patterns[:1]:  # Check the load pattern
        if re.search(pattern, route_content):
            has_json_body = True
            break
    
    if has_json_body:
        # Extract all property names accessed from the JSON body
        for pattern in body_patterns[1:]:  # Skip the first pattern (load pattern)
            body_matches = re.finditer(pattern, route_content)
            for match in body_matches:
                param_name = match.group(1)
                if param_name not in params['body'] and param_name:
                    params['body'].append(param_name)
    
    # Special case: check for specific patterns in your code
    if "/checkName" in route_path:
        # For your specific route, ensure Name is captured
        if "Name" not in params['body']:
            params['body'].append("Name")
    
    return params

def find_crow_routes(directory):
    """Scan all .cpp files in directory for Crow routes and their parameters."""
    routes = []
    
    # Read the entire file content first to handle multiline routes
    for filepath in Path(directory).glob("*.cpp"):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Find route declarations with their implementations
            # This pattern matches CROW_ROUTE with method specification and captures the implementation
            route_pattern = r'(CROW_ROUTE\s*\([^,]+,\s*"([^"]+)"\s*\)(?:\s*\.methods\s*\(\s*"([^"]+)"_method\s*\))?\s*\(\[\]\s*\([^)]*\)\s*\{([^}]+)\})'
            
            for match in re.finditer(route_pattern, content, re.DOTALL):
                full_match = match.group(1)
                route = match.group(2)
                
                # Skip excluded routes
                if should_exclude_route(route):
                    print(f"Excluding route: {route}")
                    continue
                
                # Determine HTTP method
                method = match.group(3).lower() if match.group(3) else "get"
                
                # Get the route implementation body
                route_body = match.group(4)
                
                # Extract parameters from the route body
                params = extract_parameters(route_body, route)
                
                routes.append({
                    'path': route,
                    'method': method,
                    'file': filepath.name,
                    'params': params
                })
                
                print(f"Found route: {method} {route} in {filepath.name}")
                if params['query']:
                    print(f"  Query params: {params['query']}")
                if params['body']:
                    print(f"  Body params: {params['body']}")
                    
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
    
    return routes

def generate_parameter_schema(params):
    """Generate OpenAPI parameter schema from extracted parameters."""
    yaml = ""
    
    # Query parameters
    if params['query']:
        for param in params['query']:
            yaml += f"""        - name: {param}
          in: query
          required: true
          schema:
            type: string
          description: {param} parameter
"""
    else:
        yaml += "        []\n"
    
    return yaml

def generate_request_body_schema(params):
    """Generate OpenAPI request body schema for JSON body parameters."""
    if not params['body']:
        return ""
    
    yaml = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
"""
    
    # Mark all body parameters as required (since your code expects them)
    for param in params['body']:
        yaml += f"""                - {param}
"""
    
    yaml += """              properties:
"""
    
    for param in params['body']:
        yaml += f"""                {param}:
                  type: string
                  description: {param} value
                  example: "example_{param}"
"""
    
    return yaml

def generate_openapi_yaml(routes, output_file="openapi.yaml"):
    """Generate OpenAPI YAML from found routes with parameters."""
    
    yaml_content = """openapi: 3.0.0
info:
  title: Crow API
  description: Auto-generated API documentation with parameter support
  version: 1.0.0
servers:
  - url: http://localhost:6969
    description: Local server
paths:
"""
    
    for route in routes:
        path_entry = f"""  {route['path']}:
    {route['method']}:
      summary: {route['method'].upper()} {route['path']}
      description: Auto-generated endpoint from {route['file']}
      parameters:
"""
        
        # Add parameters
        path_entry += generate_parameter_schema(route['params'])
        
        # Add request body if there are body parameters
        path_entry += generate_request_body_schema(route['params'])
        
        # Add responses
        path_entry += """      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
        '400':
          description: Bad request - missing or invalid parameters
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
    
    # Find all routes with parameters
    print("Scanning for Crow routes and parameters...")
    routes = find_crow_routes(script_dir)
    
    if not routes:
        print("No Crow routes found in .cpp files (excluding Swagger UI routes)")
        return
    
    # Generate YAML
    generate_openapi_yaml(routes, output_file)
    
    # Print found routes with parameters
    print("\nFound routes with parameters (excluding Swagger UI):")
    for route in routes:
        print(f"  {route['method'].upper():<6} {route['path']}")
        if route['params']['query']:
            print(f"        Query params: {', '.join(route['params']['query'])}")
        if route['params']['body']:
            print(f"        Body params: {', '.join(route['params']['body'])}")

if __name__ == "__main__":
    main()