import psycopg2

def get_db_connection():
    return psycopg2.connect(
        "postgresql://klresolute_whatsapp_mvp_db_user:9TxwOCle7eWPEM5jTYRrh76JFZ9aA0R9@dpg-d58n7l0gjchc73a9c280-a.singapore-postgres.render.com:5432/klresolute_whatsapp_mvp_db"
    )