
import os
import json
from utils.database import DatabaseManager

def update_forms_to_0_10_scale():
    """Update all forms to use 0-10 rating scale"""
    
    # Initialize database
    db = DatabaseManager()
    
    forms_dir = 'Forms'
    updated_count = 0
    
    print("🔄 Iniciando atualização da escala de ratings...")
    
    # Update file-based forms
    if os.path.exists(forms_dir):
        for filename in os.listdir(forms_dir):
            if filename.endswith('.json'):
                form_id = filename[:-5]
                file_path = os.path.join(forms_dir, filename)
                
                try:
                    # Read form data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        form_data = json.load(f)
                    
                    # No changes needed to JSON structure
                    # The template already handles 0-10 range
                    # Just ensure form is saved to database
                    
                    # Save to database
                    if db.save_form(form_id, form_data):
                        print(f"✅ Formulário {form_id} atualizado no banco de dados")
                        updated_count += 1
                    else:
                        print(f"⚠️ Erro ao atualizar {form_id} no banco")
                        
                except Exception as e:
                    print(f"❌ Erro ao processar {filename}: {str(e)}")
    
    print(f"\n✨ Atualização concluída! {updated_count} formulários processados.")
    print("\n📝 Nota: Os formulários já usarão a escala 0-10 automaticamente,")
    print("pois o template HTML foi atualizado. Este script apenas garantiu")
    print("que todos os formulários estão sincronizados com o banco de dados.")

if __name__ == '__main__':
    update_forms_to_0_10_scale()
