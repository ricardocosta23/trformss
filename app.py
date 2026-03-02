import os
import logging
import time
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.middleware.proxy_fix import ProxyFix
import json
import tempfile
import uuid
from datetime import datetime
import threading
from utils.monday_api import MondayAPI
# Import API modules
from api.formguias import formguias_bp
from api.formclientes import formclientes_bp  
from api.formfornecedores import formfornecedores_bp

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)

# Create Flask app.
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key-for-development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# In-memory storage for forms (since Vercel is read-only)
FORMS_STORAGE = {}
CONFIG_STORAGE = {
    "guias": {
        "board_a": "",
        "board_b": "",
        "link_column": "",
        "questions": []
    },
    "clientes": {
        "board_a": "",
        "board_b": "",
        "link_column": "",
        "questions": []
    },
    "fornecedores": {
        "board_a": "",
        "board_b": "",
        "link_column": "",
        "questions": []
    }
}

# Global configuration cache
config_cache = None
config_last_modified = None

def load_config():
    """Load configuration from JSON file with caching"""
    global config_cache, config_last_modified

    config_path = os.path.join(os.path.dirname(__file__), 'setup', 'config.json')

    try:
        # Check if file has been modified
        current_modified = os.path.getmtime(config_path)

        if config_cache is None or config_last_modified != current_modified:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_cache = json.load(f)
                config_last_modified = current_modified
                app.logger.info("Configuration loaded/reloaded from file")

        return config_cache

    except FileNotFoundError:
        app.logger.warning("Config file not found, using default configuration")
        return {}
    except json.JSONDecodeError as e:
        app.logger.error(f"Error parsing config file: {str(e)}")
        return {}

def save_config(config):
    """Save configuration (in development only)"""
    global config_cache, config_last_modified
    try:
        if not os.environ.get('VERCEL'):  # Only save in development
            os.makedirs('setup', exist_ok=True)
            with open('setup/config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            # Update cache after successful save
            config_cache = config.copy()
            config_last_modified = time.time()
        else:
            # In production, update the cache but warn about persistence
            config_cache = config.copy()
            config_last_modified = time.time()
            app.logger.warning("Production environment: Configuration saved to memory only. Changes will not persist across deployments.")
    except Exception as e:
        app.logger.error(f"Error saving configuration: {str(e)}")

# Register blueprints
app.register_blueprint(formguias_bp)
app.register_blueprint(formclientes_bp)
app.register_blueprint(formfornecedores_bp)

@app.route('/')
def index():
    """Home page with navigation to admin interface"""
    return render_template('base.html')

@app.route('/admin')
def admin():
    """Admin interface for managing form configurations"""
    config = load_config()
    return render_template('admin.html', config=config)

@app.route('/api/config', methods=['GET', 'POST'])
def config_api():
    """API endpoint for managing configurations"""
    if request.method == 'GET':
        try:
            # Load configuration directly from config.json file
            config_path = os.path.join('setup', 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                app.logger.info("Configuration loaded successfully from config.json")
                return jsonify(config)
            else:
                app.logger.error("config.json not found")
                return jsonify({"error": "Configuration file not found"}), 404
        except Exception as e:
            app.logger.error(f"Error loading config: {str(e)}")
            return jsonify({"error": "Failed to load configuration"}), 500

    elif request.method == 'POST':
        try:
            config_data = request.get_json()

            # Update the cache first
            global config_cache, config_last_modified
            config_cache = config_data.copy()
            config_last_modified = time.time()

            # Check if we're in Vercel environment first
            if os.environ.get('VERCEL'):
                app.logger.info("Configuration saved to memory only (Vercel environment)")
                return jsonify({
                    "success": True,
                    "message": "Configuration saved to memory only. Changes will not persist across deployments.",
                    "warning": "Running in production mode. For persistent changes, update the configuration file and redeploy."
                })
            else:
                # Only try to write to file in development environment
                try:
                    config_path = os.path.join(os.path.dirname(__file__), 'setup', 'config.json')
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)

                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)

                    app.logger.info("Configuration saved successfully to config.json")
                    return jsonify({
                        "success": True,
                        "message": "Configuration saved successfully to config.json"
                    })
                except Exception as file_error:
                    app.logger.warning(f"Could not save to file, using memory only: {str(file_error)}")
                    return jsonify({
                        "success": True,
                        "message": "Configuration saved to memory only (file system read-only)",
                        "warning": "Configuration could not be saved to file. Changes will not persist across restarts."
                    })
        except Exception as e:
            app.logger.error(f"Error saving configuration: {str(e)}")
            return jsonify({"error": f"Failed to save configuration: {str(e)}"}), 500

@app.route('/api/reload_config', methods=['POST'])
def reload_config():
    """Reload configuration from file"""
    try:
        # Clear any cached configuration
        global config_cache
        config_cache = None

        # Load fresh configuration
        config = load_config()

        return jsonify({
            "success": True,
            "message": "Configuration reloaded successfully",
            "config": config
        })
    except Exception as e:
        app.logger.error(f"Error reloading config: {str(e)}")
        return jsonify({"error": "Failed to reload configuration"}), 500

@app.route('/api/forms/<form_id>', methods=['DELETE'])
def delete_form(form_id):
    """API endpoint to delete a form"""
    try:
        if form_id in FORMS_STORAGE:
            del FORMS_STORAGE[form_id]
            return jsonify({"message": "Form deleted successfully"})
        else:
            return jsonify({"error": "Form not found"}), 404
    except Exception as e:
        app.logger.error(f"Error deleting form {form_id}: {str(e)}")
        return jsonify({"error": "Failed to delete form"}), 500

@app.route('/form/<form_id>')
def display_form(form_id):
    """Display generated form"""
    try:
        app.logger.info(f"Attempting to display form: {form_id}")
        
        from utils.form_generator import FormGenerator
        form_generator = FormGenerator()
        form_data = form_generator.get_form_data(form_id)

        if not form_data:
            app.logger.error(f"Form {form_id} not found in storage or files")
            return render_template('base.html', error_message=f"Form {form_id} not found"), 404

        app.logger.info(f"Form {form_id} found, checking if active")

        # Add fallback for missing instructions_text field (for forms created before this field was added)
        if not form_data.get('instructions_text'):
            form_type = form_data.get('type')
            if form_type == 'guias':
                form_data['instructions_text'] = """Pedimos sua avaliação sobre nossos serviços. A pesquisa segue a metodologia NPS (Net Promoter Score)
0 a 10:  9 ou 10 = Promotores (satisfeitos e recomendam);  
7 ou 8 = Neutros (satisfeitos, mas sem lealdade);  
0 a 6 = Detratores (insatisfeitos, afetam a reputação).  
Sua participação é essencial para nossa melhoria contínua."""
            elif form_type == 'clientes':
                form_data['instructions_text'] = """Pedimos sua avaliação sobre nossos serviços. A pesquisa segue a metodologia NPS (Net Promoter Score)
0 a 10:  9 ou 10 = Promotores (satisfeitos e recomendam);  
7 ou 8 = Neutros (satisfeitos, mas sem lealdade);  
0 a 6 = Detratores (insatisfeitos, afetam a reputação).  
Sua participação é essencial para nossa melhoria contínua."""
            elif form_type == 'fornecedores':
                form_data['instructions_text'] = """Pedimos sua avaliação sobre nossos serviços. A pesquisa segue a metodologia NPS (Net Promoter Score)
0 a 10:  9 ou 10 = Promotores (satisfeitos e recomendam);  
7 ou 8 = Neutros (satisfeitos, mas sem lealdade);  
0 a 6 = Detratores (insatisfeitos, afetam a reputação).  
Sua participação é essencial para nossa melhoria contínua."""

        # Check if form is active
        is_active = form_data.get('is_active', True)  # Default to active for existing forms

        if not is_active:
            app.logger.info(f"Form {form_id} is inactive, showing inactive page")
            # Show inactive form page
            return render_template('inactive_form.html', form_data=form_data, form_id=form_id)

        app.logger.info(f"Form {form_id} is active, displaying form")

        # Load current configuration to ensure latest settings
        config = load_config()
        form_data['config'] = config

        return render_template('form_template.html', form_data=form_data, form_id=form_id)
    except Exception as e:
        app.logger.error(f"Error displaying form {form_id}: {str(e)}")
        return render_template('base.html', error_message=f"Error loading form: {str(e)}"), 500

def process_form_background(form_id, submission_data, stored_form_data):
    """Background processing function for form submission"""
    try:
        app.logger.info(f"Background processing started for form {form_id}")

        # Load configuration
        config = load_config()
        form_type = stored_form_data.get('type')
        form_config = config.get(form_type, {})

        app.logger.info(f"Processing - Form type: {form_type}, Config: {form_config}")

        if form_config.get('board_b'):
            from utils.monday_api import MondayAPI
            monday_api = MondayAPI()

            # Get the item ID from webhook data
            webhook_data = stored_form_data.get('webhook_data', {})
            item_id = webhook_data.get('event', {}).get('pulseId')
            board_b = form_config['board_b']

            app.logger.info(f"Processing - Saving responses to Board B: {board_b}, Item ID: {item_id}")

            if item_id and board_b:
                # Prepare all column values for batch creation
                column_values = {}
                header_data = stored_form_data.get('header_data', {})
                item_name = header_data.get('Viagem') or webhook_data.get('event', {}).get('pulseName', 'Resposta do Formulário')

                # Add header data to column values
                if header_data.get('Destino'):
                    column_values['text_mkrb17ct'] = header_data['Destino']

                if header_data.get('Data'):
                    column_values['text_mksq2j87'] = header_data['Data']

                if header_data.get('Cliente'):
                    column_values['text_mkrjdnry'] = header_data['Cliente']

                # Add mirror column value to destination board
                if header_data.get('MirrorColumnValue'):
                    column_values['text_mkrkqj1g'] = header_data['MirrorColumnValue']

                # Process all questions and add to column values
                for question in stored_form_data.get('questions', []):
                    question_id = question.get('id')
                    destination_column = question.get('destination_column')
                    question_destination_column = question.get('question_destination_column')
                    text_destination_column = question.get('text_destination_column')
                    rating_destination_column = question.get('rating_destination_column')
                    question_type = question.get('type')

                    # Skip divider questions
                    if question_type == 'divider':
                        continue

                    # For Monday column questions, save both the response and the column value
                    if question_type == 'monday_column':
                        # Save the user's response (rating)
                        response_value = submission_data.get(question_id)
                        if response_value is not None and str(response_value).strip():
                            response_str = str(response_value).strip()

                            # Convert English to Portuguese
                            if response_str.lower() == "yes":
                                response_str = "Sim"
                            elif response_str.lower() == "no":
                                response_str = "Não"

                            # Save to rating destination column
                            if rating_destination_column and rating_destination_column.strip():
                                column_values[rating_destination_column.strip()] = response_str

                        # Save the column value (question text) to text destination column
                        if text_destination_column and text_destination_column.strip():
                            column_value = question.get('column_value', '')
                            if column_value and column_value not in ['', 'Dados não encontrados', 'Erro ao carregar dados', 'Dados não disponíveis', 'Configuração incompleta']:
                                column_values[text_destination_column.strip()] = column_value

                    else:
                        # For regular questions (yesno, rating, text, longtext, dropdown)
                        response_value = submission_data.get(question_id)

                        if response_value is not None:
                            response_str = str(response_value).strip()

                            if response_str:
                                # Convert English to Portuguese
                                if response_str.lower() == "yes":
                                    response_str = "Sim"
                                elif response_str.lower() == "no":
                                    response_str = "Não"

                                # Truncate long text fields to 2000 characters
                                if question_type == 'longtext' and len(response_str) > 2000:
                                    app.logger.warning(f"Truncating long text from {len(response_str)} to 2000 chars for column {destination_column}")
                                    response_str = response_str[:2000]

                                if destination_column and destination_column.strip():
                                    # Validate numeric columns
                                    if destination_column.startswith('numeric_'):
                                        # Only save if it's a valid number
                                        try:
                                            # Try to convert to float to validate
                                            float(response_str)
                                            column_values[destination_column.strip()] = response_str
                                        except ValueError:
                                            app.logger.warning(f"Skipping invalid numeric value '{response_str}' for column {destination_column}")
                                            # Skip invalid numeric values instead of failing the whole submission
                                    else:
                                        # For non-numeric columns, save as is
                                        column_values[destination_column.strip()] = response_str

                # Create item with all values in a single request
                app.logger.info(f"Processing - Creating item with {len(column_values)} column values")
                app.logger.info(f"Column values: {column_values}")

                create_result = monday_api.create_item_with_values(board_b, item_name, column_values)

                if create_result and create_result.get('create_item', {}).get('id'):
                    new_item_id = create_result['create_item']['id']
                    app.logger.info(f"Processing - Successfully created item with ID: {new_item_id} and all column values")
                else:
                    app.logger.error("Processing - Failed to create item in Board B with values")

            else:
                app.logger.error("Processing - Missing item_id or board_b configuration")
        else:
            app.logger.warning(f"Processing - No board_b configured for form type: {form_type}")

    except Exception as e:
        app.logger.error(f"Background processing error for form {form_id}: {str(e)}")


@app.route('/submit_form/<form_id>', methods=['POST'])
def submit_form(form_id):
    """Handle form submission"""
    try:
        # Get form data using FormGenerator to ensure file-based forms are loaded
        from utils.form_generator import FormGenerator
        form_generator = FormGenerator()
        form_data = form_generator.get_form_data(form_id)

        if not form_data:
            return jsonify({"error": "Form not found"}), 404

        # Get submission data
        submission_data = request.get_json()

        app.logger.info(f"Form submission for {form_id}: {submission_data}")

        # Load configuration
        config = load_config()
        form_type = form_data.get('type')

        # Monday API setup
        from utils.monday_api import MondayAPI
        monday_api = MondayAPI()

        # Get the item ID from webhook data
        webhook_data = form_data.get('webhook_data', {})
        item_id = webhook_data.get('event', {}).get('pulseId')

        form_responses = submission_data  # Assuming submission data is a dict of question_id: response

        # Process form submission using the background processor for better reliability
        try:
            # Store form type in session for success page styling
            session['last_form_type'] = form_data.get('type', 'guias')

            process_form_background(form_id, submission_data, form_data)

            return jsonify({
                "success": True,
                "message": "Formulário enviado com sucesso! As respostas foram salvas no Monday.com.",
                "redirect_url": url_for('success')
            })
        except Exception as processing_error:
            app.logger.error(f"Error processing form: {str(processing_error)}")
            # Still return success to user but log the error
            return jsonify({
                "success": True,
                "message": "Formulário enviado com sucesso! As respostas estão sendo processadas."
            })

    except Exception as e:
        app.logger.error(f"Error submitting form: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@app.route('/activation', methods=['POST'])
def handle_activation():
    """Handle form activation/deactivation webhook"""
    try:
        # Get webhook data
        data = request.get_json()

        # Handle Monday.com webhook challenge validation
        if data and 'challenge' in data:
            challenge = data['challenge']
            return jsonify({'challenge': challenge})

        webhook_data = data
        app.logger.info(f"Received activation webhook data: {webhook_data}")

        # Extract webhook event data
        event = webhook_data.get('event', {})
        item_id = event.get('pulseId')

        if not item_id:
            app.logger.error("No item ID found in webhook data")
            return jsonify({"error": "No item ID found"}), 400

        # Initialize Monday.com API
        from utils.monday_api import MondayAPI
        monday_api = MondayAPI()

        # Query Monday.com to get the current column values for this item
        item_data = monday_api.get_item_column_values(item_id)

        if not item_data:
            app.logger.error(f"Could not fetch item data for item {item_id}")
            return jsonify({"error": "Could not fetch item data"}), 400

        # Extract form URLs from multiple columns and status from color_mkt5gs90 column
        form_urls = []
        form_status = ""

        # Define the form URL columns to check
        form_url_columns = ['text_mksvzfm1', 'text_mksw9b2r', 'text_mkspdyty']

        for column in item_data.get('column_values', []):
            column_id = column.get('id')
            if column_id in form_url_columns:  # Form URL columns
                form_url = monday_api.get_column_value(column)
                if form_url and form_url.strip():
                    form_urls.append(form_url.strip())
            elif column_id == 'color_mkt5gs90':  # Status column
                form_status = monday_api.get_column_value(column)

        app.logger.info(f"Queried Monday.com - Form URLs: {form_urls}, Status: {form_status}")

        if not form_urls:
            app.logger.error(f"No form URLs found in any form URL columns for item {item_id}")
            return jsonify({"error": "No form URLs found in form URL columns"}), 400

        # Determine if forms should be active
        is_active = form_status.lower() == 'ativo'

        # Process each form URL
        processed_forms = []
        from utils.database import DatabaseManager
        db = DatabaseManager()

        import re
        for form_url in form_urls:
            # Extract form ID from URL (assuming URL format: .../form/{form_id})
            form_id_match = re.search(r'/form/([^/?]+)', form_url)
            if not form_id_match:
                app.logger.warning(f"Could not extract form ID from URL: {form_url}")
                continue

            form_id = form_id_match.group(1)
            app.logger.info(f"Processing form ID: {form_id}")

            # Check if form exists in database
            form_data = db.get_form(form_id)
            if not form_data:
                app.logger.warning(f"Form {form_id} not found in database, skipping")
                continue

            # Update form activation status in database
            update_success = db.update_form_activation(form_id, is_active)
            
            if update_success:
                processed_forms.append({
                    'form_id': form_id,
                    'form_url': form_url,
                    'is_active': is_active
                })

                status_text = "ativado" if is_active else "desativado"
                app.logger.info(f"Form {form_id} has been {status_text} in database based on Monday.com column value")
            else:
                app.logger.error(f"Failed to update activation status for form {form_id}")

        if not processed_forms:
            app.logger.error("No valid forms were processed")
            return jsonify({"error": "No valid forms found to process"}), 400

        status_text = "ativados" if is_active else "desativados"
        app.logger.info(f"{len(processed_forms)} forms have been {status_text} based on Monday.com column value")

        return jsonify({
            "success": True,
            "message": f"{len(processed_forms)} forms have been {status_text}",
            "processed_forms": processed_forms,
            "is_active": is_active,
            "status_from_monday": form_status
        })

    except Exception as e:
        app.logger.error(f"Error handling activation webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500




@app.route('/success')
def success():
    """Display success page after form submission"""
    # Get form type from session (set during form submission)
    form_type = session.get('last_form_type', 'guias')
    return render_template('success.html', form_type=form_type)

@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

# Store form data function for use by API modules
def store_form_data(form_id, form_data):
    """Store form data in memory"""
    FORMS_STORAGE[form_id] = form_data
    return True

def get_form_data(form_id):
    """Get form data from memory"""
    return FORMS_STORAGE.get(form_id)

# Make these functions and storage available to other modules
app.store_form_data = store_form_data
app.get_form_data = get_form_data
app.load_config = load_config
app.FORMS_STORAGE = FORMS_STORAGE



@app.route('/api/forms', methods=['GET'])
def list_forms():
    """List all generated forms"""
    try:
        from utils.form_generator import FormGenerator
        form_generator = FormGenerator()
        forms = form_generator.list_all_forms()
        return jsonify(forms)
    except Exception as e:
        app.logger.error(f"Error listing forms: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/debug/forms')
def debug_forms():
    """Debug endpoint to check form availability"""
    try:
        from utils.form_generator import FormGenerator
        import os
        
        form_generator = FormGenerator()
        
        # Check database status
        db_status = form_generator.db.get_connection_status()
        
        # Check file system
        forms_dir = 'Forms'
        file_forms = []
        if os.path.exists(forms_dir):
            file_forms = [f[:-5] for f in os.listdir(forms_dir) if f.endswith('.json')]
        
        # Check memory
        memory_forms = list(FORMS_STORAGE.keys()) if FORMS_STORAGE else []
        
        # Get all forms via FormGenerator
        all_forms = form_generator.list_all_forms()
        
        debug_info = {
            "database_status": db_status,
            "total_forms_in_files": len(file_forms),
            "total_forms_in_memory": len(memory_forms),
            "total_forms_via_generator": len(all_forms),
            "forms_in_files": file_forms[:10],  # Show first 10
            "forms_in_memory": memory_forms[:10],  # Show first 10
            "sample_forms": all_forms[:5]  # Show first 5 with details
        }
        
        return jsonify(debug_info)
    except Exception as e:
        app.logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/debug/database')
def debug_database():
    """Debug endpoint specifically for database status"""
    try:
        from utils.database import DatabaseManager
        db = DatabaseManager()
        
        status = db.get_connection_status()
        connection_check = db.check_connection()
        
        debug_info = {
            "connection_status": status,
            "connection_healthy": connection_check,
            "database_url_exists": bool(os.environ.get('DATABASE_URL')),
            "database_url_starts_with": os.environ.get('DATABASE_URL', '')[:20] + "..." if os.environ.get('DATABASE_URL') else None
        }
        
        return jsonify(debug_info)
    except Exception as e:
        app.logger.error(f"Error in database debug endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Load all existing forms into memory on startup
def load_existing_forms():
    """Load all existing forms from files into memory on startup"""
    try:
        from utils.form_generator import FormGenerator
        import os
        
        form_generator = FormGenerator()
        forms_dir = 'Forms'
        
        if os.path.exists(forms_dir):
            for filename in os.listdir(forms_dir):
                if filename.endswith('.json'):
                    form_id = filename[:-5]  # Remove .json extension
                    form_data = form_generator._load_form_from_file(form_id)
                    if form_data:
                        FORMS_STORAGE[form_id] = form_data
                        app.logger.info(f"Loaded form {form_id} into memory")
            
            app.logger.info(f"Loaded {len(FORMS_STORAGE)} forms into memory on startup")
    except Exception as e:
        app.logger.error(f"Error loading existing forms: {str(e)}")

# Load forms on startup
load_existing_forms()

@app.route('/api/create-manual-item', methods=['POST'])
def create_manual_item():
    """API endpoint to manually create items on Monday.com Board B"""
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        form_type = data.get('form_type')
        column_values = data.get('column_values')

        if not item_name or not form_type or not column_values:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: item_name, form_type, or column_values'
            }), 400

        # Load configuration
        config = load_config()
        
        # Get Board B ID for the form type
        board_b = config.get(form_type, {}).get('board_b')
        
        if not board_b:
            return jsonify({
                'success': False,
                'error': f'Board B not configured for form type: {form_type}'
            }), 400

        # Validate numeric columns
        validated_columns = {}
        for col_id, value in column_values.items():
            if col_id.startswith('numeric_'):
                # Validate numeric values
                try:
                    float(str(value))
                    validated_columns[col_id] = str(value)
                except ValueError:
                    app.logger.warning(f"Skipping invalid numeric value '{value}' for column {col_id}")
                    # Skip invalid numeric values
                    continue
            else:
                # Keep non-numeric values as is
                validated_columns[col_id] = str(value)

        # Create item using Monday.com API
        monday_api = MondayAPI()
        result = monday_api.create_item_with_values(board_b, item_name, validated_columns)

        if result and result.get('create_item', {}).get('id'):
            item_id = result['create_item']['id']
            app.logger.info(f"Manual item created successfully: ID {item_id}, Board: {board_b}")
            return jsonify({
                'success': True,
                'item_id': item_id,
                'board_id': board_b
            })
        else:
            app.logger.error(f"Failed to create manual item on Board {board_b}")
            return jsonify({
                'success': False,
                'error': 'Failed to create item on Monday.com'
            }), 500

    except Exception as e:
        app.logger.error(f"Error in manual item creation: {str(e)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)