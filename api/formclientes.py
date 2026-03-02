import os
import json
import logging
from flask import Blueprint, request, jsonify
from utils.monday_api import MondayAPI
from utils.form_generator import FormGenerator

formclientes_bp = Blueprint('formclientes', __name__)

@formclientes_bp.route('/formclientes', methods=['POST'])
def handle_formclientes():
    """Handle webhook for Clientes forms"""
    try:
        # Get webhook data
        data = request.get_json()

        # Handle Monday.com webhook challenge validation
        if data and 'challenge' in data:
            challenge = data['challenge']
            return jsonify({'challenge': challenge})

        webhook_data = data
        logging.info(f"Received webhook data for Clientes: {webhook_data}")

        # Load configuration dynamically
        with open('setup/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        clientes_config = config.get('clientes', {})

        if not clientes_config.get('questions'):
            return jsonify({"error": "No questions configured for Clientes"}), 400

        # Initialize Monday.com API
        monday_api = MondayAPI()

        # Fetch header data from Monday.com with specific columns
        header_data = {}
        if clientes_config.get('board_a'):
            try:
                # Extract item ID from webhook data
                item_id = webhook_data.get('event', {}).get('pulseId')
                if item_id:
                    # Get specific item data from Monday.com
                    item_data = monday_api.get_item_column_values(item_id)

                    if item_data:
                        # Set Viagem as the item name
                        header_data['Viagem'] = item_data.get('name', '')

                        # Map specific columns to header fields
                        column_mapping = {
                            'lookup_mkrjh91x': 'Destino',
                            'lookup_mkrjpdz0': 'Data',
                            'lookup_mkrb9ns5': 'Cliente',
                            'lookup_mkrkwqep': 'MirrorColumnValue'  # For destination board
                        }

                        # Extract column values
                        for column in item_data.get('column_values', []):
                            column_id = column.get('id')
                            if column_id in column_mapping:
                                header_field = column_mapping[column_id]
                                column_value = monday_api.get_column_value(column)
                                if column_value:
                                    # Always format dates in header data to dd/mm/yyyy
                                    if header_field in ['Data', 'Data da Viagem', 'Data do Serviço', 'Data do Contrato'] or monday_api.is_date_like(column_value):
                                        formatted_date = monday_api.format_date_to_dd_mm_yyyy(column_value)
                                        header_data[header_field] = formatted_date if formatted_date else column_value
                                        logging.info(f"Header date formatted: '{column_value}' -> '{formatted_date}'")
                                    else:
                                        header_data[header_field] = column_value

                        logging.info(f"Header data collected: {header_data}")
            except Exception as e:
                logging.error(f"Error fetching header data: {str(e)}")

        # Process questions and populate Monday column data
        processed_questions = []
        for question in clientes_config['questions']:
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

                    logging.info(f"Clientes - Fetching Monday column data - Item ID: {item_id}, Column: {source_column}, Board: {clientes_config['board_a']}")

                    if item_id and source_column and clientes_config.get('board_a'):
                        try:
                            # Get specific item data from Monday.com
                            item_data = monday_api.get_item_column_values(item_id)

                            logging.info(f"Clientes - Item data received: {item_data is not None}")
                            if item_data:
                                logging.info(f"Clientes - Item columns: {[col.get('id') for col in item_data.get('column_values', [])]}")

                            if item_data and item_data.get('column_values'):
                                # Find column value
                                column_value = ""
                                for column in item_data.get('column_values', []):
                                    logging.info(f"Clientes - Checking column: {column.get('id')} vs {source_column}")
                                    if column.get('id') == source_column:
                                        column_value = monday_api.get_column_value(column)
                                        logging.info(f"Clientes - Found column value: '{column_value}' from column data: {column}")
                                        break

                                # Always set column_value, even if empty
                                processed_question['column_value'] = column_value if column_value else ""
                                logging.info(f"Clientes - Set column_value to: '{processed_question['column_value']}'")

                                # Ensure destination_column is set for Monday column questions
                                if not processed_question.get('destination_column'):
                                    processed_question['destination_column'] = source_column
                                    logging.info(f"Clientes - Set destination_column to: '{source_column}'")

                                # Ensure text_destination_column and rating_destination_column are set from config
                                if not processed_question.get('text_destination_column') and question.get('text_destination_column'):
                                    processed_question['text_destination_column'] = question.get('text_destination_column')
                                    logging.info(f"Clientes - Set text_destination_column to: '{question.get('text_destination_column')}'")

                                if not processed_question.get('rating_destination_column') and question.get('rating_destination_column'):
                                    processed_question['rating_destination_column'] = question.get('rating_destination_column')
                                    logging.info(f"Clientes - Set rating_destination_column to: '{question.get('rating_destination_column')}')")
                            else:
                                logging.warning("Clientes - No item data or column values received from Monday.com")
                                processed_question['column_value'] = ""
                        except Exception as api_error:
                            logging.error(f"Clientes - Monday.com API error: {str(api_error)}")
                            processed_question['column_value'] = ""
                    else:
                        logging.warning(f"Clientes - Missing required data - item_id: {item_id}, source_column: {source_column}, board_a: {clientes_config.get('board_a')}")
                        processed_question['column_value'] = ""
                except Exception as e:
                    logging.error(f"Clientes - Error fetching Monday column data: {str(e)}")
                    processed_question['column_value'] = ""

            processed_questions.append(processed_question)

        # Generate form
        form_generator = FormGenerator()

        # Instructions text for Clientes forms
        instructions_text = """Pedimos sua avaliação sobre nossos serviços. A pesquisa segue a metodologia NPS (Net Promoter Score)
0 a 10:  9 ou 10 = Promotores (satisfeitos e recomendam);  
7 ou 8 = Neutros (satisfeitos, mas sem lealdade);  
0 a 6 = Detratores (insatisfeitos, afetam a reputação).  
Sua participação é essencial para nossa melhoria contínua."""

        form_data = {
            "type": "clientes",
            "title": "Pesquisa de Satisfação - Convidados",
            "subtitle": "Avalie como foi sua experiência",
            "questions": processed_questions,
            "header_data": header_data,
            "webhook_data": webhook_data,
            "instructions_text": instructions_text
        }

        form_id = form_generator.generate_form(form_data)
        form_url = f"{request.host_url}form/{form_id}"

        # Update Monday.com board if configured
        # Use board_a (source board) for the form link, since that's where the webhook originates
        if clientes_config.get('board_a') and clientes_config.get('link_column'):
            try:
                # Extract item ID from webhook data
                item_id = webhook_data.get('event', {}).get('pulseId')
                board_id = webhook_data.get('event', {}).get('boardId')
                if item_id and board_id:
                    monday_api.update_item_column(
                        board_id=board_id,  # Use the board ID from webhook
                        item_id=item_id,
                        column_id=clientes_config['link_column'],
                        value=form_url
                    )
                    logging.info(f"Updated Monday.com board {board_id} with form URL")
            except Exception as e:
                logging.error(f"Failed to update Monday.com: {str(e)}")

        return jsonify({
            "success": True,
            "form_url": form_url,
            "form_id": form_id,
            "message": "Form generated successfully for Clientes"
        })

    except Exception as e:
        logging.error(f"Error handling Clientes webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500