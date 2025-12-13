from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0007_cascade_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Eliminar el constraint antiguo de user_id
                ALTER TABLE api_transcription 
                DROP CONSTRAINT api_transcription_user_id_6fbf78cc_fk_auth_user_id;
                
                -- Crear el constraint nuevo con CASCADE
                ALTER TABLE api_transcription 
                ADD CONSTRAINT api_transcription_user_id_6fbf78cc_fk_auth_user_id 
                FOREIGN KEY (user_id) 
                REFERENCES auth_user(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Rollback: volver al constraint sin CASCADE
                ALTER TABLE api_transcription 
                DROP CONSTRAINT api_transcription_user_id_6fbf78cc_fk_auth_user_id;
                
                ALTER TABLE api_transcription 
                ADD CONSTRAINT api_transcription_user_id_6fbf78cc_fk_auth_user_id 
                FOREIGN KEY (user_id) 
                REFERENCES auth_user(id) 
                DEFERRABLE INITIALLY DEFERRED;
            """
        ),
    ]