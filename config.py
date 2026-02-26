import os
from dotenv import load_dotenv
import time
import glob
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    
    # Application configuration
    TMP_DIR = os.path.join(os.getenv('TEMP', '/tmp'), 'diagrams_webui')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    RATE_LIMIT = "100 per minute"  # Rate limit for API endpoints
    DIAGRAM_CLEANUP_AGE = 5  # minutes
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Ensure the temp directory exists
    os.makedirs(TMP_DIR, exist_ok=True)
    
    @classmethod
    def cleanup_old_diagrams(cls):
        """Remove diagram files older than DIAGRAM_CLEANUP_AGE minutes"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=cls.DIAGRAM_CLEANUP_AGE)
            files_removed = 0
            for file_path in glob.glob(os.path.join(cls.TMP_DIR, '*.png')):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        files_removed += 1
                    except Exception as e:
                        print(f"Error removing old diagram {file_path}: {e}")
            if files_removed > 0:
                print(f"Cleanup: Removed {files_removed} old diagram files")
        except Exception as e:
            print(f"Error during diagram cleanup: {e}")
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler('logs/pydraw.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('PyDraw startup')
        
        # Schedule periodic cleanup
        def cleanup_task():
            while True:
                try:
                    cutoff_time = datetime.now() - timedelta(minutes=Config.DIAGRAM_CLEANUP_AGE)
                    files_removed = 0
                    for file_path in glob.glob(os.path.join(Config.TMP_DIR, '*.png')):
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if file_time < cutoff_time:
                            try:
                                os.remove(file_path)
                                files_removed += 1
                            except Exception as e:
                                app.logger.error(f"Error removing old diagram {file_path}: {e}")
                    if files_removed > 0:
                        app.logger.info(f"Cleanup: Removed {files_removed} old diagram files")
                except Exception as e:
                    app.logger.error(f"Error during diagram cleanup: {e}")
                time.sleep(60)  # Check every minute
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
