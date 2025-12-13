
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0006_transcription_temp_custom_prompt'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Eliminar el constraint antiguo
                ALTER TABLE api_summary 
                DROP CONSTRAINT api_summary_transcription_id_47ccd6da_fk_api_transcription_id;
                
                -- Crear el constraint nuevo con CASCADE
                ALTER TABLE api_summary 
                ADD CONSTRAINT api_summary_transcription_id_47ccd6da_fk_api_transcription_id 
                FOREIGN KEY (transcription_id) 
                REFERENCES api_transcription(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Rollback: volver al constraint sin CASCADE
                ALTER TABLE api_summary 
                DROP CONSTRAINT api_summary_transcription_id_47ccd6da_fk_api_transcription_id;
                
                ALTER TABLE api_summary 
                ADD CONSTRAINT api_summary_transcription_id_47ccd6da_fk_api_transcription_id 
                FOREIGN KEY (transcription_id) 
                REFERENCES api_transcription(id) 
                DEFERRABLE INITIALLY DEFERRED;
            """
        ),
    ]