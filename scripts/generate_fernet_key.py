from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()
print(f"SMTP_CREDENTIALS_KEY={key}")
