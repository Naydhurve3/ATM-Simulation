import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from flask import Flask
from src.dashboard.routes import register_routes

def create_dashboard(data_analysis=None, data_visualization=None, user_manager=None, user_data=None):
    app = Flask(__name__, template_folder='templates')
    app.config['data_analysis'] = data_analysis
    app.config['data_visualization'] = data_visualization
    app.config['user_manager'] = user_manager
    app.config['user_data'] = user_data
    register_routes(app)
    return app

def run_dashboard(host='127.0.0.1', port=5000, debug=False, **kwargs):
    app = create_dashboard(**kwargs)
    import webbrowser
    webbrowser.open(f'http://{host}:{port}')
    app.run(host=host, port=port, debug=debug)
