import os
import json
import logging
from flask import Blueprint, request, jsonify
from utils.monday_api import MondayAPI
from utils.form_generator import FormGenerator

formfornecedores_bp = Blueprint('formfornecedores', __name__)

@formfornecedores_bp.route('/formfornecedores', methods=['POST'])
def handle_fornecedores_webhook():
    """Handle Monday.com webhook for Fornecedores forms"""
    try:
        # Get webhook data
        data = request.get_json()

        # Handle Monday.com webhook challenge validation
        if data and 'challenge' in data:
            challenge = data['challenge']
            return jsonify({'challenge': challenge})

        webhook_data = data
        logging.info(f"Received Fornecedores webhook: {webhook_data}")

        # Load configuration
        with open('setup/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        fornecedores_config = config.get('fornecedores', {})

        if not fornecedores_config.get('board_a') or not fornecedores_config.get('questions'):
            return jsonify({"error": "Fornecedores configuration not complete"}), 400

        # Extract webhook information
        event = webhook_data.get('event', {})
        item_id = event.get('pulseId')
        item_name = event.get('pulseName', 'Fornecedor')

        if not item_id:
            return jsonify({"error": "Item ID not found in webhook"}), 400

        # Generate form
        form_generator = FormGenerator()

        # Instructions text for Fornecedores forms
        instructions_text = """Pedimos sua avaliação sobre nossos serviços. A pesquisa segue a metodologia NPS (Net Promoter Score)
0 a 10:  9 ou 10 = Promotores (satisfeitos e recomendam);  
7 ou 8 = Neutros (satisfeitos, mas sem lealdade);  
0 a 6 = Detratores (insatisfeitos, afetam a reputação).  
Sua participação é essencial para nossa melhoria contínua."""

        # Prepare form data
        form_data = {
            "type": "fornecedores",
            "title": f"Avaliação do Cliente",
            "subtitle": "Por favor, preencha este formulário para avaliar o fornecedor",
            "questions": fornecedores_config.get('questions', []),
            "webhook_data": webhook_data,
            "item_id": item_id,
            "item_name": item_name,
            "instructions_text": instructions_text
        }

        # Get Monday.com data if needed
        monday_api = MondayAPI()

        # Fetch header data from Monday.com with specific columns
        header_data = {}
        if fornecedores_config.get('board_a'):
            try:
                # Get specific item data from Monday.com using the working method
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

        # Add header data to form
        form_data['header_data'] = header_data

        # Ensure all rating questions are required
        for question in form_data['questions']:
            if question.get('type') == 'rating':
                question['required'] = True
        
        # Process questions and add Monday column data
        if monday_api.api_token:
            try:
                item_data = monday_api.get_item_by_id(fornecedores_config['board_a'], item_id)
                if item_data:
                    # Add column values to form questions
                    for question in form_data['questions']:
                        if question.get('type') == 'monday_column':
                            source_column = question.get('source_column')
                            if source_column:
                                # Find column value
                                column_value = ""
                                for column in item_data.get('column_values', []):
                                    if column.get('id') == source_column:
                                        column_value = monday_api.get_column_value(column)
                                        break

                                # Always set column_value, even if empty
                                question['column_value'] = column_value if column_value else ""

                                # Ensure destination_column is set for Monday column questions
                                if not question.get('destination_column'):
                                    question['destination_column'] = source_column
                                    logging.info(f"Fornecedores - Set destination_column to: '{source_column}'")
            except Exception as e:
                logging.error(f"Error fetching Monday column data: {str(e)}")

        form_id = form_generator.generate_form(form_data)

        # Generate form URL
        form_url = f"{request.host_url}form/{form_id}"

        # Update Monday.com with form link if configured
        # Use board_a (source board) for the form link, since that's where the webhook originates
        if fornecedores_config.get('board_a') and fornecedores_config.get('link_column'):
            try:
                # Extract item ID from webhook data
                item_id = webhook_data.get('event', {}).get('pulseId')
                board_id = webhook_data.get('event', {}).get('boardId')
                if item_id and board_id:
                    monday_api.update_item_column(
                        board_id=board_id,  # Use the board ID from webhook
                        item_id=item_id,
                        column_id=fornecedores_config['link_column'],
                        value=form_url
                    )
                    logging.info(f"Updated Monday.com board {board_id} with form URL")
            except Exception as e:
                logging.error(f"Failed to update Monday.com: {str(e)}")

        return jsonify({
            "message": "Fornecedores form generated successfully",
            "form_id": form_id,
            "form_url": form_url
        })

    except Exception as e:
        logging.error(f"Error processing Fornecedores webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500