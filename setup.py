import json

print("Welcome to the Qr-Gate setup!")
company_name = input("Please enter your Company's Name: ")
app_secret = input("Please enter app Password: ")

print(".........................................................................................")

email_smtp_server = input("Please enter your smtp server address: ")
email_smtp_port = input("Please enter your smtp port: ")
email_smtp_username = input("Please enter your smtp username (EMAIL): ")
email_smtp_password = input("Please enter your smtp password (PASSWORD TO EMAIL INBOX): ")

print("Great thanks! Data is being processed...")

data = {
    "company_name": company_name,
    "email_smtp_server": email_smtp_server,
    "email_smtp_username": email_smtp_username,
    "email_smtp_password": email_smtp_password,
    "email_smtp_port": email_smtp_port,
    "app_secret": app_secret
}

# Öffne die Datei im Schreibmodus und schreibe die JSON-Daten
with open("static/data/config.qrconf", "w") as config_file:
    config_file.truncate(0)
    json.dump(data, config_file, indent=4)

print("Success! All data provided has been successfully saved!")
