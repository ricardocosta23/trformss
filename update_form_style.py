
import os
import json
from utils.database import DatabaseManager

def update_form_style():
    """Update specific form to have light grey background without images"""
    
    form_id = "794ffc62-9728-4955-9092-aefd1a98c236"
    
    # Initialize database
    db = DatabaseManager()
    
    print(f"🔄 Updating form {form_id} styling...")
    
    try:
        # Get current form data
        form_data = db.get_form_with_status(form_id)
        
        if not form_data:
            print(f"❌ Form {form_id} not found in database")
            return False
        
        print(f"✅ Found form: {form_data.get('title', 'Unknown')}")
        
        # Update form styling to light grey background
        # This will override the default background for this specific form
        form_data['custom_style'] = "background: #f5f5f5 !important;"
        
        # Ensure form type is set (this controls CSS class)
        if 'type' not in form_data or form_data['type'] == 'clientes':
            # Keep as clientes type which already uses light grey
            form_data['type'] = 'clientes'
            print("✅ Form type set to 'clientes' (light grey background)")
        
        # Save updated form back to database
        if db.save_form(form_id, form_data):
            print(f"✅ Form {form_id} updated successfully!")
            print(f"   - Background: Light grey (#f5f5f5)")
            print(f"   - No background image")
            print(f"   - No purple styling")
            return True
        else:
            print(f"❌ Failed to save form {form_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating form: {str(e)}")
        return False

if __name__ == '__main__':
    update_form_style()
