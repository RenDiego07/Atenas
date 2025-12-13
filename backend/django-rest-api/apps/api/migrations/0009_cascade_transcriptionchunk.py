# Generated migration for CASCADE constraint on api_transcriptionchunk

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0008_fix_user_cascade'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop the existing constraint
                ALTER TABLE api_transcriptionchunk 
                DROP CONSTRAINT api_transcriptionchu_transcription_id_30698877_fk_api_trans;
                
                -- Create the constraint with CASCADE
                ALTER TABLE api_transcriptionchunk 
                ADD CONSTRAINT api_transcriptionchu_transcription_id_30698877_fk_api_trans 
                FOREIGN KEY (transcription_id) 
                REFERENCES api_transcription(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Rollback: revert to constraint without CASCADE
                ALTER TABLE api_transcriptionchunk 
                DROP CONSTRAINT api_transcriptionchu_transcription_id_30698877_fk_api_trans;
                
                ALTER TABLE api_transcriptionchunk 
                ADD CONSTRAINT api_transcriptionchu_transcription_id_30698877_fk_api_trans 
                FOREIGN KEY (transcription_id) 
                REFERENCES api_transcription(id) 
                DEFERRABLE INITIALLY DEFERRED;
            """
        ),
    ]