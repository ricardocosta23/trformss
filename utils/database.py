
import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Use Replit's PostgreSQL database URL if available
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                print("Conectando ao banco...")
                # Convert postgresql:// to postgres:// for psycopg2 compatibility
                if database_url.startswith('postgresql://'):
                    database_url = database_url.replace('postgresql://', 'postgres://', 1)
                self.connection = psycopg2.connect(database_url)
                self.logger.info("Connected to PostgreSQL database")
            else:
                self.logger.warning("No DATABASE_URL found, forms will use file storage only")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
    
    def _create_tables(self):
        """Create forms table if it doesn't exist"""
        if not self.connection:
            return
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS forms (
                        id VARCHAR PRIMARY KEY,
                        form_data JSONB NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Add is_active column to existing tables if it doesn't exist
                cursor.execute("""
                    ALTER TABLE forms 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
                """)
                self.connection.commit()
                self.logger.info("Forms table ready with is_active column")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
    
    def save_form(self, form_id, data):
        """Insert or update a form in the database"""
        if not self.connection:
            self.logger.error("No database connection available")
            return False
        
        try:
            # Test connection first
            with self.connection.cursor() as test_cursor:
                test_cursor.execute("SELECT 1")
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO forms (id, form_data) 
                    VALUES (%s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET form_data = %s, updated_at = CURRENT_TIMESTAMP
                """, (form_id, json.dumps(data), json.dumps(data)))
                self.connection.commit()
                self.logger.info(f"Successfully saved form '{form_id}' to database")
                
                # Verify the save by checking if we can retrieve it
                cursor.execute("SELECT COUNT(*) FROM forms WHERE id = %s", (form_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    self.logger.info(f"Verified form '{form_id}' exists in database")
                    return True
                else:
                    self.logger.error(f"Form '{form_id}' was not found after saving")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to save form '{form_id}' to database: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def get_form(self, form_id):
        """Get form data by ID from database"""
        if not self.connection:
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT form_data FROM forms WHERE id = %s", (form_id,))
                result = cursor.fetchone()
                if result:
                    return result['form_data']
        except Exception as e:
            self.logger.error(f"Failed to get form from database: {str(e)}")
        
        return None
    
    def list_forms(self):
        """List all forms from database"""
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, created_at FROM forms ORDER BY created_at DESC")
                results = cursor.fetchall()
                return [{'id': result['id'], 'name': result['id']} for result in results]
        except Exception as e:
            self.logger.error(f"Failed to list forms from database: {str(e)}")
            return []
    
    def delete_form(self, form_id):
        """Delete form from database by ID"""
        if not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM forms WHERE id = %s", (form_id,))
                self.connection.commit()
                self.logger.info(f"Deleted form '{form_id}' from database")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete form from database: {str(e)}")
            return False
    
    def check_connection(self):
        """Check if database connection is healthy"""
        if not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    def update_form_activation(self, form_id, is_active):
        """Update form activation status in database"""
        if not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE forms 
                    SET is_active = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (is_active, form_id))
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    status = "activated" if is_active else "deactivated"
                    self.logger.info(f"Form '{form_id}' {status} in database")
                    return True
                else:
                    self.logger.warning(f"No form found with ID '{form_id}' to update")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to update form activation '{form_id}': {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def get_form_with_status(self, form_id):
        """Get form data with activation status"""
        if not self.connection:
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT form_data, is_active FROM forms WHERE id = %s", (form_id,))
                result = cursor.fetchone()
                if result:
                    form_data = result['form_data']
                    form_data['is_active'] = result['is_active']
                    return form_data
        except Exception as e:
            self.logger.error(f"Failed to get form with status from database: {str(e)}")
        
        return None

    def get_connection_status(self):
        """Get detailed connection status for debugging"""
        if not self.connection:
            return {"connected": False, "error": "No connection object"}
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM forms")
                form_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM forms WHERE is_active = true")
                active_forms = cursor.fetchone()[0]
                return {
                    "connected": True,
                    "version": version,
                    "form_count": form_count,
                    "active_forms": active_forms
                }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    # Legacy methods for backward compatibility with existing code
    def save_form_by_id(self, form_id, form_data):
        """Legacy method: save form using ID"""
        return self.save_form(form_id, form_data)
    
    def get_form_by_id(self, form_id):
        """Legacy method: get form using ID"""
        return self.get_form(form_id)
