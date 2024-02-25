import json

print("Welcome to the Qr-Gate setup!")
print(">> BASIC INFO <<")
company_name = input("Please enter your Company's Name: ")
app_secret = input("Please enter app Password: ")
t_price = input("Please enter the Ticket Price: ")

print(".........................................................................................")
print(">> EMAIL SETUP <<")

email_smtp_server = input("Please enter your smtp server address: ")
email_smtp_port = input("Please enter your smtp port: ")
email_smtp_username = input("Please enter your smtp username (EMAIL): ")
email_smtp_password = input("Please enter your smtp password (PASSWORD TO EMAIL INBOX): ")

print(".........................................................................................")
#print(">> STRIPE PAYMENT SETUP <<")

#stripe_api_skey = input("Please enter your Stripe Secret KEY: ")
#stripe_api_pkey = input("Please enter your Stripe Public KEY: ")

print(".........................................................................................")
print(">> 1st ADMIN USER SETUP <<")

admin_agentnummer = input("Please enter your admin agent number: ")
admin_agentname = input("Please enter your admin agent name: ")

print("Great thanks! Data is being processed...")

data = {
    "company_name": company_name,
    "email_smtp_server": email_smtp_server,
    "email_smtp_username": email_smtp_username,
    "email_smtp_password": email_smtp_password,
    "email_smtp_port": email_smtp_port,
    "app_secret": app_secret,
    #"stripe_api_skey": stripe_api_skey,
    #"stripe_api_pkey": stripe_api_pkey,
    "admin_agent": admin_agentnummer,
    "admin_agentname": admin_agentname,
    "ticket_price": t_price
}

# Öffne die Datei im Schreibmodus und schreibe die JSON-Daten
with open("static/data/config.qrconf", "w") as config_file:
    config_file.truncate(0)
    json.dump(data, config_file, indent=4)
    config_file.close()

eventdates = open("static/data/eventdates.qrconf")
eventdates.close()

shopbarrier = open("static/data/shopbarrier.qrconf")
shopbarrier.close()

print("Success! All data provided has been successfully saved!")
