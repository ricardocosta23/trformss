
import json
from utils.database import DatabaseManager

def recover_form(form_id):
    """Attempt to recover a form from the database"""
    db = DatabaseManager()
    
    # Get form data from database
    form_data = db.get_form_with_status(form_id)
    
    if form_data:
        print(f"Form found in database!")
        print(f"Form Type: {form_data.get('type')}")
        print(f"Form Title: {form_data.get('title')}")
        print(f"Active Status: {form_data.get('is_active')}")
        print(f"\nNumber of questions: {len(form_data.get('questions', []))}")
        
        # Save to a recovery file
        recovery_filename = f"Forms/{form_id}_RECOVERED.json"
        with open(recovery_filename, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nForm saved to: {recovery_filename}")
        print("\nTo restore this form to the database, you can:")
        print(f"1. Review the recovered file")
        print(f"2. Use db.save_form('{form_id}', form_data) to restore it")
        
        return True
    else:
        print(f"Form {form_id} not found in database")
        return False

if __name__ == "__main__":
    form_id = "0e76eff8-152a-4d26-aab3-6aabf63abcf1"
    print(f"Attempting to recover form: {form_id}\n")
    recover_form(form_id)
