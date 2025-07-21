
import os
import psycopg2
from config import Config

def export_schema():
    """Export database schema to a file"""
    try:
        # Connect to database
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        # Get all table definitions
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        schema_output = []
        schema_output.append("-- Database Schema Export")
        schema_output.append(f"-- Generated on: {__import__('datetime').datetime.now()}")
        schema_output.append("")
        
        # Export enum types
        cur.execute("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            ORDER BY t.typname, e.enumsortorder;
        """)
        
        enums = cur.fetchall()
        current_enum = None
        
        for enum_name, enum_value in enums:
            if current_enum != enum_name:
                if current_enum is not None:
                    schema_output.append(");")
                    schema_output.append("")
                schema_output.append(f"CREATE TYPE {enum_name} AS ENUM (")
                current_enum = enum_name
                schema_output.append(f"    '{enum_value}'")
            else:
                schema_output.append(f"    ,'{enum_value}'")
        
        if current_enum:
            schema_output.append(");")
            schema_output.append("")
        
        # Export table schemas
        for table in tables:
            table_name = table[0]
            
            # Get table definition
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            
            schema_output.append(f"CREATE TABLE {table_name} (")
            
            for i, (col_name, data_type, is_nullable, col_default) in enumerate(columns):
                nullable = "" if is_nullable == "YES" else " NOT NULL"
                default = f" DEFAULT {col_default}" if col_default else ""
                comma = "," if i < len(columns) - 1 else ""
                
                schema_output.append(f"    {col_name} {data_type}{nullable}{default}{comma}")
            
            schema_output.append(");")
            schema_output.append("")
        
        # Write to file
        with open('exported_schema.sql', 'w') as f:
            f.write('\n'.join(schema_output))
        
        print("Schema exported successfully to 'exported_schema.sql'")
        
    except Exception as e:
        print(f"Error exporting schema: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    export_schema()
