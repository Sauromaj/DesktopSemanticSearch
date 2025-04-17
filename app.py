import os
import logging
from datetime import datetime
from config import ApplicationConfig
from ui_manager import UIManager
from document_processor import DocumentProcessor
from search_engine import SearchEngine
from vector_store import VectorStore
from pathlib import Path
import shutil
import platform
import subprocess

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("semantic_search")

try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
    from werkzeug.utils import secure_filename
except ImportError:
    # Fallback for environments without Flask
    logger.error("Flask dependencies not available. Simulating web environment for development.")
    
    # Define minimal classes to allow code to load without Flask
    class Flask:
        def __init__(self, *args, **kwargs):
            self.config = {}
            self.template_filter_funcs = {}
            self.routes = {}
            self.secret_key = None
        
        def route(self, rule, **options):
            def decorator(f):
                self.routes[rule] = f
                return f
            return decorator
        
        def template_filter(self, name=None):
            def decorator(f):
                self.template_filter_funcs[name or f.__name__] = f
                return f
            return decorator
        
        def run(self, **kwargs):
            logger.info("Flask app would start here in a real environment")
    
    def render_template(template, **context):
        logger.info(f"Would render {template} with {context}")
        return f"<html><body>Template: {template}</body></html>"
    
    def redirect(url):
        logger.info(f"Would redirect to {url}")
        return url
    
    def url_for(endpoint, **values):
        return f"/{endpoint}"
    
    def flash(message, category='message'):
        logger.info(f"Flash message: {message} [{category}]")
    
    def jsonify(data):
        import json
        return json.dumps(data)
    
    class secure_filename:
        @staticmethod
        def __call__(filename):
            return filename.replace(' ', '_')

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure uploads
UPLOAD_FOLDER = 'uploads'
DESKTOP_FOLDER = 'Desktop'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DESKTOP_FOLDER'] = DESKTOP_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Define template filters
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert a Unix timestamp to formatted date string"""
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Sample data to simulate indexed documents
sample_documents = [
    {
        'path': 'documents/report1.pdf',
        'filename': 'report1.pdf',
        'extension': '.pdf',
        'content_preview': 'This is a quarterly financial report with budget details...',
        'similarity': 0.85,
        'last_modified': 1618456789,
        'size': 1024000
    },
    {
        'path': 'documents/presentation.pptx',
        'filename': 'presentation.pptx',
        'extension': '.pptx',
        'content_preview': 'Marketing plan for Q3 2024 focusing on new product launches...',
        'similarity': 0.75,
        'last_modified': 1618456789,
        'size': 2048000
    },
    {
        'path': 'documents/data.xlsx',
        'filename': 'data.xlsx',
        'extension': '.xlsx',
        'content_preview': 'Sales data broken down by region and product category...',
        'similarity': 0.68,
        'last_modified': 1618456789,
        'size': 512000
    }
]

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """Format file size from bytes to a human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
# Initialize the document processor and search engine
config_setup = ApplicationConfig()
ui_manager_setup = UIManager()
doc_processor = DocumentProcessor(config_setup, ui_manager_setup)

vector_store_setup = VectorStore(config_setup.DEFAULTS['vector_db_path'])
search_engine = SearchEngine(vector_store_setup, ui_manager_setup, config_setup)

# # Loop through the uploads folder and call the remove_document function for each file
# for filename in os.listdir(app.config['UPLOAD_FOLDER']):
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     if os.path.isfile(file_path):
#         vector_store_setup.remove_document(file_path)
#         logger.info(f"Removed document from vector store: {file_path}")

# # Reload any documents in uploads currently
# upload_folder_path = Path(os.path.join(app.config['UPLOAD_FOLDER']))
# doc_processor.index_directory(upload_folder_path, force = True)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads for indexing"""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        files = request.files.getlist('file')
        
        if not files or files[0].filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        success_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                success_count += 1
                logger.info(f"Saved file: {file_path}")
            else:
                flash(f'File type not allowed: {file.filename}')
        
        if success_count > 0:
            flash(f'Successfully uploaded {success_count} file(s)')
            # In a real app, we would call the document processor to index the files here
            upload_folder_path = Path(os.path.join(app.config['UPLOAD_FOLDER']))
            doc_processor.index_directory(upload_folder_path)
            vector_store_setup.reload_index()

        return redirect(url_for('upload_file'))
            
        
    
    # List already uploaded files
    uploaded_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)
            uploaded_files.append({
                'filename': filename,
                'path': file_path,
                'size': format_file_size(file_stat.st_size),
                'last_modified': file_stat.st_mtime
            })
    
    return render_template('upload.html', files=uploaded_files)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Handle search requests"""
    query = request.args.get('query', '')
    results = []
    
    if query:
        # In a real app, we would call the search engine here
        # For now, we'll return sample data
        results = search_engine.search(query)
    
    return render_template('search.html', query=query, results=results)

@app.route('/config', methods=['GET', 'POST'])
def config():
    """Configuration page"""
    if request.method == 'POST':
        # Handle configuration updates
        flash('Configuration updated successfully')
        return redirect(url_for('config'))
    
    # Sample configuration
    config_settings = {
        'data_dir': '/app/data',
        'vector_db_path': '/app/data/vector_db',
        'embedding_model': 'all-MiniLM-L6-v2',
        'chunk_size': 1000,
        'chunk_overlap': 200
    }
    
    return render_template('config.html', config=config_settings)

@app.route('/reindex', methods=['GET'])
def reindex():
    
    upload_folder_path = Path(os.path.join(os.path.expanduser("~"), app.config['DESKTOP_FOLDER']))
    logger.info(f"Reindexing main folder: {upload_folder_path}")

    # Index the main desktop folder
    ret_val = doc_processor.index_directory(upload_folder_path)
    if not ret_val:
        flash(f"Some error occurred while reindexing folder: {upload_folder_path}")
    else:
        # Recursively reindex all subfolders within the desktop folder
        for subfolder in upload_folder_path.rglob('*'):
            if subfolder.is_dir():
                logger.info(f"Reindexing subfolder: {subfolder}")
                ret_val = doc_processor.index_directory(subfolder)

                if not ret_val:
                    flash(f"Some error occurred while reindexing subfolder: {subfolder}")
                    break

    vector_store_setup.reload_index()
    flash("All files and subfolders reindexed successfully")

    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/handle-file', methods=['POST'])
def open_file():
    """Handle file opening requests from the frontend."""
    try:
        # Parse the JSON data from the request
        data = request.get_json()
        logger.info(f"Received data: {data}")  # Log the received data

        file_path = data.get('path')
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404

        # Open the file using the system's default application
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', file_path], check=True)

        logger.info(f"File opened successfully: {file_path}")
        return jsonify({'message': 'File opened successfully'}), 200

    except Exception as e:
        logger.error(f"Error opening file: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

@app.route('/handle-folder', methods=['POST'])
def open_folder():

    try:
        # Parse the JSON data from the request
        data = request.get_json()
        logger.info(f"Received data: {data}")  # Log the received data

        file_path = data.get('path')
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404

        # Get the folder containing the file and open it using the system's default file explorer
        folder_path = os.path.dirname(file_path)
        if platform.system() == 'Windows':
            os.startfile(folder_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', folder_path], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', folder_path], check=True)

        logger.info(f"Folder opened successfully: {folder_path}")
        return jsonify({'message': 'Folder opened successfully'}), 200

    except Exception as e:
        logger.error(f"Folder opening file: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)