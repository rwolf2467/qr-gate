import json
import random
import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, jsonify
from qrcode.main import QRCode

shopbarrier_file_path = './static/data/shopbarrier.qrconf'


def read_shopbarrier_status():
    try:
        with open(shopbarrier_file_path, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 0


def write_shopbarrier_status(status):
    with open(shopbarrier_file_path, 'w') as file:
        file.write(str(status))


print("Starting QR-Gate Server...")
print(f"Boot: {date.today()}")


def read_config():
    try:
        with open("static/data/config.qrconf", 'r') as file:
            config_data = json.load(file)
        return config_data
    except FileNotFoundError:
        return 0


app = Flask(__name__, static_folder="static", template_folder="web")
app.secret_key = read_config()['app_secret']

password_data = {
    f"{read_config()['admin_agent']}": f"{read_config()['admin_agentname']}",
    "3648": "TestUser2",
    "7900": "TestUser3"
}

smtp_server = read_config()["email_smtp_server"]
smtp_port = read_config()["email_smtp_port"]  # Port für SMTP-Server
smtp_username = read_config()["email_smtp_username"]
smtp_password = read_config()["email_smtp_password"]
sender_email = read_config()["email_smtp_username"]
version = "1.2"

print(f"Server Version: {version}")


def read_codes():
    try:
        with open("codes.json", "r") as file:
            codes_data = json.load(file)
        return codes_data
    except FileNotFoundError:
        return {}


def write_codes(codes_data):
    with open("codes.json", "w") as file:
        json.dump(codes_data, file)


def generate_ticket(ticket_number):
    size = 600  # Größe des Bildes
    ticket_img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(ticket_img)
    font = ImageFont.load_default()

    # Text "Ihr Ticket - {ticket nummer}" oben in der Mitte hinzufügen
    title_text = f"  Dein Ticket - {ticket_number}"
    title_powerdby = "Powerd by QrGate"
    title_font = ImageFont.truetype("arial.ttf", 36)
    title2_font = ImageFont.truetype("arial.ttf", 12)
    text_x = 150
    text_y = 50
    draw.text((text_x, text_y), title_text, fill="black", font=title_font)
    text_x += 100
    text_y += 50
    draw.text((text_x, text_y), title_powerdby, fill="black", font=title2_font)

    # Aufgeteilter Anweisungstext
    instruction_text1 = "Um das Ticket einzulösen, halte den unteren QR Code vor den"
    instruction_text2 = "Ticket Scanner am Eingang des Saals."
    instruction_font = ImageFont.truetype("arial.ttf", 18)  # Beispiel für eine Schriftart (Arial)
    text_x = 50
    text_y = 200
    draw.text((text_x, text_y), instruction_text1, fill="black", font=instruction_font)
    text_y += 30  # Zeilenabstand erhöhen
    draw.text((text_x, text_y), instruction_text2, fill="black", font=instruction_font)

    # QR-Code erstellen
    qr = QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(str(ticket_number))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # QR-Code hinzufügen
    qr_x = 200
    qr_y = 350
    ticket_img.paste(qr_img, (qr_x, qr_y))

    # Ticketnummer hinzufügen
    ticket_number_text = f"Ticket Nummer: {ticket_number}"
    text_x = 200
    text_y = 560
    draw.text((text_x, text_y), ticket_number_text, fill="black", font=font)

    # Speichern Sie das Ticket-Bild
    ticket_image_path = f"static/tickets/ticket_{ticket_number}.png"
    ticket_img.save(ticket_image_path)

    return ticket_image_path


@app.route('/API/check_password', methods=['POST'])
def check_password():
    data = request.json
    password = data.get('password')

    if password in password_data:
        user = password_data[password]
        print(user)
        return jsonify({"success": True, "user": user}), 200
    else:
        return jsonify({"success": False}), 401


@app.route('/app/admin-panel')
def ticket_setup():
    return render_template('admin-panel.html', data=password_data)  # noqa


@app.route("/")
def home():
    with open("static/data/config.qrconf", "r") as config_file:
        config = json.load(config_file)

        # Render das Template und übergebe die Werte aus der JSON-Datei
    return render_template('index.html', config=config)  # noqa


@app.route("/API/ping")
def pingAPI(): # noqa
    return f"<p>Server is up and running</p> <br> <p> QR-Gate Server Version:  {version}</p>"


@app.route("/app/handheld")
def admin_handheld():
    return render_template("handheld.html")  # noqa


@app.route('/API/shopbarrier_get', methods=['GET'])
def get_shopbarrier_status():
    status = read_shopbarrier_status()
    return jsonify({'value': status})


@app.route('/API/shopbarrier_set', methods=['POST'])
def set_shopbarrier_status():
    data = request.json
    value = data.get('value')
    if value is not None and isinstance(value, int):
        write_shopbarrier_status(value)
        return jsonify({'message': 'Shopbarrier status updated successfully'})
    else:
        return jsonify({'error': 'Invalid value provided'}), 400


@app.route('/API/dates_set', methods=['POST'])
def set_event_dates():
    data = request.get_json()

    if not data or 'startDate' not in data or 'endDate' not in data:
        return jsonify({'error': 'Start date and end date are required.'}), 400

    try:
        start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please provide dates in YYYY-MM-DD format.'}), 400

    all_dates = get_dates_in_range(start_date, end_date)

    file_path = './static/data/eventdates.qrconf'
    with open(file_path, 'w') as file:
        for date in all_dates: # noqa
            file.write(f'{date.strftime("%Y-%m-%d")}\n')

    return jsonify({'message': 'Dates saved successfully.'}), 200


def get_dates_in_range(start_date, end_date):
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    return dates


@app.route("/API/enable_ticket", methods=['POST'])
def enable_ticket():
    code = request.json.get('code')
    code_json = read_codes()
    if str(code) not in code_json:
        return jsonify({"success": False, "message": "Code does not exist"})
    else:
        if not code_json[code]["payed"]:
            code_json[code]["payed"] = True
            write_codes(code_json)
            return jsonify({"success": True, "message": "Successfully marked as payed"}), 200
        else:
            return jsonify({"success": False, "message": "Already Marked as Payed"}), 200


@app.route("/API/Ticket_info", methods=['POST'])
def ticket_info():
    code = request.json.get('code')
    code_json = read_codes()
    if str(code) in code_json:
        name = code_json[str(code)]["name"]
        datum = code_json[str(code)]["valid-date"]
        usercount = code_json[str(code)]["user_count"]
        used = code_json[str(code)]["used"]
        bezahlt = code_json[str(code)]["payed"]
        email = code_json[str(code)]["email"]
        preis = int(usercount) * 13
        last_used = code_json[str(code)]["last-used"]
        last_payed = code_json[str(code)]["last-payed"]
        return jsonify({"success": True, "message": "Ticket exists!",
                        'nummer': code,
                        'name': name,
                        'email': email,
                        'datum': datum,
                        'usercount': usercount,
                        'used': used,
                        'bezahlt': bezahlt,
                        'preis': preis,
                        'last_used': last_used,
                        'last_payed': last_payed
                        })
    else:
        return jsonify({"success": False, "message": "Ticket does not exist!"})


@app.route("/API/handheld/check", methods=["POST"])
def handheldcheck():
    code = request.json.get("result")
    codes_data = read_codes()

    if str(code) in codes_data:
        if str(date.today()) == str(codes_data[str(code)]["valid-date"]):
            if not codes_data[str(code)]["used"]:
                if codes_data[str(code)]["payed"]:
                    user_count = codes_data[str(code)]["user_count"]

                    data = {"success": True, "message": "Person Count: " + user_count}
                    codes_data[str(code)]["used"] = True
                    codes_data[str(code)]["last-used"] = str(date.today())
                    print(data)
                    write_codes(codes_data)
                    return jsonify(data), 200

                else:
                    data = {"success": False, "message": "Not Payed"}
                    print(data)
                    return jsonify(data), 500
            else:
                data = {"success": False, "message": "Already used"}
                print(data)
                return jsonify(data), 500
        else:
            valid_date = codes_data[str(code)]["valid-date"]
            data = {"success": False, "message": "Valid Date: " + valid_date}
            print(data)
            return jsonify(data), 500
    else:
        data = {"success": False, "message": "Ticket does not exist"}
        print(data)
        return jsonify(data), 500


@app.route("/API/create_ticket", methods=["POST"])
def create_ticket():
    try:
        code = read_codes()
        ticket_code = request.form.get("code")
        if ticket_code is not None:
            ticket_number = random.randint(1000, 9999)
            while ticket_number in code:
                ticket_number = random.randint(1000, 9999)
        personcount = request.form.get("personcount")
        valid_date = date.today()
        email = request.form.get("email")

        code[ticket_number] = {"name": None,  # noqa
                               "email": email,
                               "user_count": personcount,
                               "valid-date": valid_date,
                               "used": False,
                               "payed": False,
                               "last-used": None,
                               "last-payed": date.today()}
        write_codes(code)

        ticket_image_path = generate_ticket(ticket_number) # noqa
        data = {"success": True, "message": "Ticket was created and activated successfully!"}
        return jsonify(data), 200
    except Exception as e:
        data = {"success": False, "message": f"ERROR: {e}"}
        return jsonify(data), 500


@app.route("/API/get_tickets", methods=["POST"])
def get_tickets():
    code = read_codes()
    ticket_number = random.randint(1000, 9999)
    while ticket_number in code:
        ticket_number = random.randint(1000, 9999)
    name = request.form.get("name")
    email = request.form.get("email")
    personcount = request.form.get("personcount")
    date = request.form.get("date") # noqa

    code[ticket_number] = {"name": name,
                           "email": email,
                           "user_count": personcount,
                           "valid-date": date,
                           "used": False,
                           "payed": False,
                           "last-used": None,
                           "last-payed": None}
    write_codes(code)

    ticket_image_path = generate_ticket(ticket_number)

    subject = f'Dein QrGate Ticket - {ticket_number}'

    # Erstellen Sie die E-Mail
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject

    # Fügen Sie den Text zur E-Mail hinzu
    body = (f'Hallo und Herzlich Willkommen {name}!\n\n'
            "Im Anhang befindet sich deine Digitale Zugangskarte, die noch nicht funktioniert!\n"
            "Um dein Ticket zu aktivieren, musst du dich am Tag der Veranstaltung am Eingang melden.\n\n"
            "Mithilfe des QRCodes, der sich in Anhang befindet, kannst du den Saal betreten. "
            "Wir wünschen dir viel spaß bei der Vorstellung!")
    msg.attach(MIMEText(body, 'plain'))

    with open(ticket_image_path, 'rb') as image_file:
        img = MIMEImage(image_file.read())
        img.add_header('Content-Disposition', 'attachment', filename='ticket.png')
        msg.attach(img)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        response_data = {
            "message": f"Ticket erfolgreich Aktiviert! Email erfolgreich gesendet! - TICKETNUMMER: {ticket_number}"}
        return jsonify(response_data)
    except Exception as e:
        # Ändern Sie den Rückgabewert, um eine JSON-Antwort zu senden
        response_data = {"error": f"Fehler beim Senden der E-Mail: {str(e)}"}
        return jsonify(response_data), 500


if __name__ == '__main__':
    # Starten Sie die Flask-App in einem Thread
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('certificate.crt', 'private.key')  # app.app/server.app/
    app.run(host='0.0.0.0', port=1612, ssl_context=context, debug=False)
