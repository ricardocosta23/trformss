import os
import json
import logging
from flask import Blueprint, request, jsonify
from utils.monday_api import MondayAPI
from utils.form_generator import FormGenerator

formguias_bp = Blueprint('formguias', __name__)

@formguias_bp.route('/formguias', methods=['POST'])
def handle_formguias():
    """Handle webhook for Guias forms"""
    try:
        # Get webhook data
        data = request.get_json()

        # Handle Monday.com webhook challenge validation
        if data and 'challenge' in data:
            challenge = data['challenge']
            return jsonify({'challenge': challenge})

        webhook_data = data
        logging.info(f"Received webhook data for Guias: {webhook_data}")

        # Load configuration dynamically
        try:
            with open('setup/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in config.json: {str(e)}")
            return jsonify({"error": "Configuration file has invalid JSON syntax"}), 500
        except FileNotFoundError:
            logging.error("config.json file not found")
            return jsonify({"error": "Configuration file not found"}), 500

        guias_config = config.get('guias', {})

        if not guias_config.get('questions'):
            return jsonify({"error": "No questions configured for Guias"}), 400

        # Initialize Monday.com API
        monday_api = MondayAPI()

        # Fetch header data from Monday.com with specific columns
        header_data = {}
        instructions_text = ""  # For form filling instructions
        if guias_config.get('board_a'):
            try:
                # Extract item ID from webhook data
                item_id = webhook_data.get('pulseId') or webhook_data.get('event', {}).get('pulseId')
                if item_id:
                    # Get specific item data from Monday.com using the working method
                    item_data = monday_api.get_item_column_values(item_id)

                    if item_data:
                        # Map specific columns to header fields based on config
                        header_fields_config = guias_config.get('header_fields', [])
                        
                        # Set default Viagem if item_name is not in header_fields
                        header_data['Viagem'] = item_data.get('name', '')

                        # Map additional specific columns if not in header_fields
                        additional_mapping = {
                            'text_mm0vswrr': 'Local',
                            'text_mm12sr3v': 'Cidade',
                            'date_mm0v3rx9': 'Data',
                            'text_mm0vy6n8': 'Cliente'
                        }

                        # Extract column values based on header_fields configuration
                        for field in header_fields_config:
                            title = field.get('title')
                            monday_column = field.get('monday_column')
                            
                            if monday_column == 'item_name':
                                header_data[title] = item_data.get('name', '')
                                continue

                            # Find the column in item_data
                            for column in item_data.get('column_values', []):
                                if column.get('id') == monday_column:
                                    column_value = monday_api.get_column_value(column)
                                    if column_value:
                                        # Format dates if needed
                                        if title.lower() in ['data', 'data da viagem', 'data do serviço', 'data do contrato'] or monday_api.is_date_like(column_value):
                                            formatted_date = monday_api.format_date_to_dd_mm_yyyy(column_value)
                                            header_data[title] = formatted_date if formatted_date else column_value
                                        else:
                                            header_data[title] = column_value
                                    break

                        # Extract additional mapping columns
                        for col_id, title in additional_mapping.items():
                            if title not in header_data:
                                for column in item_data.get('column_values', []):
                                    if column.get('id') == col_id:
                                        val = monday_api.get_column_value(column)
                                        if val:
                                            header_data[title] = val
                                        break

                        # Special case for instructions text
                        for column in item_data.get('column_values', []):
                            if column.get('id') == 'long_text_mkwb4jzs':
                                instructions_value = monday_api.get_column_value(column)
                                if instructions_value and instructions_value.strip():
                                    instructions_text = instructions_value
                                break

                        logging.info(f"Header data collected from config: {header_data}")
            except Exception as e:
                logging.error(f"Error fetching header data: {str(e)}")

        # Process questions to populate Monday column data
        processed_questions = []
        for question in guias_config.get('questions', []):
            processed_question = question.copy()

            # Ensure all rating questions are required
            if processed_question.get('type') == 'rating':
                processed_question['required'] = True

            # If it's a Monday column question, fetch the data
            if question.get('type') == 'monday_column' and question.get('source_column'):
                try:
                    # Extract item ID from webhook data
                    item_id = webhook_data.get('event', {}).get('pulseId')
                    source_column = question.get('source_column')

                    logging.info(f"Fetching Monday column data - Item ID: {item_id}, Column: {source_column}, Board: {guias_config['board_a']}")

                    if item_id and source_column and guias_config.get('board_a'):
                        try:
                            # Get specific item data from Monday.com
                            item_data = monday_api.get_item_column_values(item_id)

                            logging.info(f"Item data received: {item_data is not None}")
                            if item_data:
                                logging.info(f"Item columns: {[col.get('id') for col in item_data.get('column_values', [])]}")

                            if item_data and item_data.get('column_values'):
                                # Find column value
                                column_value = ""
                                for column in item_data.get('column_values', []):
                                    logging.info(f"Checking column: {column.get('id')} vs {source_column}")
                                    if column.get('id') == source_column:
                                        column_value = monday_api.get_column_value(column)
                                        logging.info(f"Found column value: '{column_value}' from column data: {column}")
                                        break

                                # Always set column_value, even if empty
                                processed_question['column_value'] = column_value if column_value else ""
                                logging.info(f"Set column_value to: '{processed_question['column_value']}'")

                                # Ensure destination_column is set for Monday column questions
                                if not processed_question.get('destination_column'):
                                    processed_question['destination_column'] = source_column
                                    logging.info(f"Set destination_column to: '{source_column}'")
                            else:
                                logging.warning("No item data or column values received from Monday.com")
                                processed_question['column_value'] = ""
                        except Exception as api_error:
                            logging.error(f"Monday.com API error: {str(api_error)}")
                            processed_question['column_value'] = ""
                    else:
                        logging.warning(f"Missing required data - item_id: {item_id}, source_column: {source_column}, board_a: {guias_config.get('board_a')}")
                        processed_question['column_value'] = ""
                except Exception as e:
                    logging.error(f"Error fetching Monday column data: {str(e)}")
                    processed_question['column_value'] = ""

            processed_questions.append(processed_question)

        # Generate form
        form_generator = FormGenerator()
        # Log instructions text for debugging
        logging.info(f"Final instructions_text value: '{instructions_text}'")
        logging.info(f"Instructions text length: {len(instructions_text) if instructions_text else 0}")
        logging.info(f"Instructions text bool: {bool(instructions_text)}")

        form_data = {
            "type": "guias",
            "title": "Formulário de Avaliação Operacional - Guias",
            "subtitle": "Avalie sua viagem com a Top Service",
            "questions": processed_questions,
            "header_data": header_data,
            "webhook_data": webhook_data,
            "instructions_text": instructions_text  # Add instructions text
        }

        # Log form_data keys to verify instructions_text is included
        logging.info(f"form_data keys: {list(form_data.keys())}")
        logging.info(f"form_data['instructions_text']: '{form_data.get('instructions_text', 'NOT FOUND')}'")

        form_id = form_generator.generate_form(form_data)
        form_url = f"{request.host_url}form/{form_id}"

        # Update Monday.com board if configured
        # Use board_a (source board) for the form link, since that's where the webhook originates
        if guias_config.get('board_a'):
            try:
                # Extract item ID from webhook data
                item_id = webhook_data.get('pulseId') or webhook_data.get('event', {}).get('pulseId')
                board_id = "18401175950"
                column_id = "text_mm12kmh0"
                
                if item_id:
                    monday_api.update_item_column(
                        board_id=board_id,
                        item_id=item_id,
                        column_id=column_id,
                        value=form_url
                    )
                    logging.info(f"Updated Monday.com board {board_id} column {column_id} with form URL: {form_url}")
            except Exception as e:
                logging.error(f"Failed to update Monday.com: {str(e)}")

        return jsonify({
            "success": True,
            "form_url": form_url,
            "form_id": form_id,
            "message": "Form generated successfully for Guias"
        })

    except Exception as e:
        logging.error(f"Error handling Guias webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
