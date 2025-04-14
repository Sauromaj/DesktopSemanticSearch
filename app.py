import os
import logging
from datetime import datetime

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
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        results = sample_documents
    
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

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)