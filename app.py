from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import tempfile
import uuid
import subprocess
import re
import shutil
import glob
import logging
from config import Config

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config.from_object(Config)
Config.init_app(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Directory to store generated images
tmp_dir = Config.TMP_DIR
os.makedirs(tmp_dir, exist_ok=True)

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal attacks"""
    # Replace spaces with underscores and remove any other potentially dangerous characters
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

def validate_diagram_code(code):
    """Validate diagram code for security"""
    if len(code) > 10000:  # Limit code size
        raise ValueError("Code too long")
    
    # Check for potentially dangerous imports
    dangerous_imports = ['os', 'sys', 'subprocess', 'eval', 'exec']
    for imp in dangerous_imports:
        if f'import {imp}' in code or f'from {imp}' in code:
            raise ValueError(f"Dangerous import detected: {imp}")
    
    return True

def patch_diagram_code(code, output_name):
    # Find the Diagram constructor call
    pattern = r'with Diagram\(([^)]*)\):'
    
    def replacer(match):
        args = match.group(1)
        # Split into positional and keyword arguments
        parts = [p.strip() for p in args.split(',')]
        positional = []
        keyword = []
        
        for part in parts:
            if '=' in part:
                # Skip the show parameter as we'll add it later
                if not part.strip().startswith('show='):
                    keyword.append(part.strip())
            else:
                positional.append(part.strip())
        
        # Build the new argument string
        new_args = []
        # Add the output name as first positional argument
        new_args.append(f'"{output_name}"')
        # Add any remaining positional arguments
        new_args.extend(positional)
        # Add show=False and other keyword arguments
        new_args.append('show=False')
        new_args.extend(keyword)
        
        return f'with Diagram({", ".join(new_args)}):'
    
    return re.sub(pattern, replacer, code)

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def index():
    image_url = None
    error = None
    default_code = '''# here's a simple example to get started
# click the "Generate Diagram" button to see the result
# or visit Docs & Examples for more examples

#include your Providers
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB 

# Construct a diagram and provide a name
# N.B. ####
# Diagram names = file names and persist for 5 minutes
# Use unique names for faster updates
with Diagram("Simple Web Service"):
# Specify your Nodes, Flows, Clusters, etc.
    ELB("lb") >> EC2("web") >> RDS("userdb")
    
# pyDraw does not support...
# jupyter notebooks
# output formats aside from png
# a few other things that are noted in the Docs
    '''
    
    code = default_code if request.method == 'GET' else request.form.get('code', '')
    if request.method == 'POST':
        if not code.strip():
            error = 'Please enter diagram code.'
        else:
            try:
                validate_diagram_code(code)
                
                # Extract the diagram name from the code
                diagram_name_match = re.search(r'with Diagram\("([^"]+)"', code)
                if not diagram_name_match:
                    error = 'Could not find diagram name in the code.'
                    return render_template('index.html', image_url=image_url, error=error, code=code)
                
                diagram_name = diagram_name_match.group(1)
                # Sanitize the diagram name to create a consistent filename
                output_name = sanitize_filename(f"{diagram_name}.png")
                
                # Save code to a temp file
                filename = f'diagram_{uuid.uuid4().hex}.py'
                filepath = os.path.join(tmp_dir, filename)
                
                try:
                    with open(filepath, 'w') as f:
                        f.write(code)
                    
                    # Patch the code to set show=False and filename=output_name
                    patched_code = patch_diagram_code(code, output_name)
                    with open(filepath, 'w') as f:
                        f.write(patched_code)
                    
                    app.logger.info(f"Running diagram code in: {tmp_dir}")
                    app.logger.info(f"Expected output file: {os.path.join(tmp_dir, output_name)}")
                    
                    result = subprocess.run(
                        ['python3', filepath],
                        check=True,
                        cwd=tmp_dir,
                        timeout=10,
                        capture_output=True,
                        text=True
                    )
                    
                    # Check for any PNG files in the directory
                    png_files = glob.glob(os.path.join(tmp_dir, '*.png'))
                    app.logger.info(f"Found PNG files: {png_files}")
                    
                    # Verify the image was created
                    image_path = os.path.join(tmp_dir, output_name)
                    if os.path.exists(image_path):
                        image_url = url_for('generated_image', filename=output_name)
                    else:
                        # Try to find the file with spaces instead of underscores
                        space_filename = output_name.replace('_', ' ')
                        space_path = os.path.join(tmp_dir, space_filename)
                        if os.path.exists(space_path):
                            # If found, rename it to our sanitized version
                            os.rename(space_path, image_path)
                            image_url = url_for('generated_image', filename=output_name)
                        else:
                            error = 'Diagram not found. Get Help if the problem persists.'
                except subprocess.CalledProcessError as e:
                    app.logger.error(f"Error generating diagram: {e.stderr or e.stdout or str(e)}")
                    error = 'Error generating diagram. Please try again. Get Help if the problem persists.'
                except Exception as e:
                    app.logger.error(f"Unexpected error: {str(e)}")
                    error = 'Unexpected error. Please try again. Get Help if the problem persists.'
                finally:
                    # Clean up temporary files
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception as e:
                        app.logger.error(f"Error cleaning up temporary file: {str(e)}")
            except ValueError as e:
                error = str(e)
                
    return render_template('index.html', image_url=image_url, error=error, code=code)

@app.route('/generated/<filename>')
@limiter.limit("30 per minute")
def generated_image(filename):
    try:
        filename = sanitize_filename(filename)
        return send_from_directory(tmp_dir, filename)
    except Exception as e:
        app.logger.error(f"Error serving image: {str(e)}")
        abort(404)

@app.route('/docs')
def docs():
    return render_template('docs.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))