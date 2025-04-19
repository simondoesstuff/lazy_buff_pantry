import json
import os
import re
import subprocess
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# ----- Init

if "config.json" not in os.listdir():
    print("Missing config.json; check README.md")
    exit(1)

conf = json.load(open("config.json"))
daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

if conf["target"]["day"] not in daysOfWeek:
    print("Invalid config.target.day, expected one of: " + ", ".join(daysOfWeek))
    exit(1)
if "username" not in conf:
    print("Missing username in config.json")
    exit(1)
if "password" not in conf:
    print("Missing password in config.json")
    exit(1)

session = requests.Session()


# ----- Authentication


fedAuth = "https://fedauth.colorado.edu/idp/profile/SAML2/POST/SSO"
pantry = "https://app.pantrysoft.com"


res = session.get(f"{pantry}/login/CUfeedthestampede").text
# -> "/saml/login?idp=https://fedauth.colorado.edu/idp/shibboleth&target=https://app.pantrysoft.com/login/CUfeedthestampede"
samlPath = re.search(r'"\/(saml\/login.*?)"', res).group(1)

res = session.get(f"{pantry}/{samlPath}").text
# -> name="SAMLRequest" value="PD94bWwgdmVyc2l..." />
samlReq = re.search(r'name="SAMLRequest"\s*value="(.*?)"', res).group(1)

session.post(f"{fedAuth}", data={"SAMLRequest": samlReq})

session.post(
    f"{fedAuth}?execution=e1s1",
    data={
        "shib_idp_ls_exception.shib_idp_session_ss": "",
        "shib_idp_ls_success.shib_idp_session_ss": "true",
        "shib_idp_ls_value.shib_idp_session_ss": "",
        "shib_idp_ls_exception.shib_idp_persistent_ss": "",
        "shib_idp_ls_success.shib_idp_persistent_ss": "true",
        "shib_idp_ls_value.shib_idp_persistent_ss": "",
        "shib_idp_ls_supported": "true",
        "_eventId_proceed": "",
    },
).text

session.post(
    f"{fedAuth}?execution=e1s2",
    data={
        "j_username": conf["username"],
        "j_password": conf["password"],
        "_eventId_proceed": "",
    },
)

res = session.post(
    f"{fedAuth}?execution=e1s3",
    data={
        "shib_idp_ls_exception.shib_idp_session_ss": "",
        "shib_idp_ls_success.shib_idp_session_ss": "true",
        "_eventId_proceed": "",
    },
).text
# -> name="SAMLResponse" value="PD94bWwgdmVyc2lvbj0iMS4..."
samlTok = re.search(r'name="SAMLResponse"\s+value="(.*?)"', res).group(1)

session.post(f"{pantry}/saml/login_check", data={"SAMLResponse": samlTok})


# ----- Current Appointment Status


def get_registrations():
    res = session.get(f"{pantry}/storefront/order_summary").text
    soup = BeautifulSoup(res, "html.parser")
    summary = soup.find("summary-page")

    if summary is None:
        return list()

    currentOrder = json.loads(summary.get(":current-order") or "{}")
    ordersJson = json.loads(summary.get(":future-orders") or "[]")

    if currentOrder is not None and "appointment" in currentOrder.keys():
        ordersJson.append(currentOrder)

    orders = list()

    for order in ordersJson:
        appt = order.get("appointment")
        if appt is None:
            continue
        apptTime = appt.get("appointmentTime")
        if apptTime is None:
            continue
        apptDate = apptTime.get("date")
        if apptDate is None:
            continue
        dt = datetime.strptime(apptDate, "%Y-%m-%d %H:%M:%S.%f")
        orders.append(dt)
    return orders


orders = get_registrations()
newAppts = [appt for appt in orders if appt >= datetime.today()]

if len(newAppts) != 0:
    newApptsStr = ", ".join([appt.strftime("%Y-%m-%d %H:%M") for appt in newAppts])
    print("Already appointed:", newApptsStr)
    exit(0)


# ----- Appointmentization


now = datetime.now()
start = datetime.now() - relativedelta(days=14)
end = datetime.now() + relativedelta(days=14)

datetimeFormat = "%Y-%m-%dT%H:%M:%S"
start = start.strftime(datetimeFormat)
end = end.strftime(datetimeFormat)

apptInfo = session.get(
    f"{pantry}/storefront/available_appointments"
    "?location=1&visitType=14"
    f"&start={start}"
    f"&end={end}",
).json()["events"]

print("Possible new appointments:")
targetAppt = None

for appt in apptInfo:
    apptStart = datetime.strptime(appt["start"], datetimeFormat)
    timeUntil = apptStart - now

    if timeUntil.days < 1:
        continue
    if appt["extendedProps"]["isFull"]:
        continue

    apptWeekDay = daysOfWeek[apptStart.weekday()]
    apptHour = apptStart.hour

    print(f"\t- {apptWeekDay} at {apptHour}")

    if apptWeekDay != conf["target"]["day"]:
        continue
    if apptHour != conf["target"]["hour"]:
        continue

    bId = appt["extendedProps"]["blockId"]
    print(f"\t\tperfect. -> bId: {bId}")

    targetAppt = {"start": re.search(r"(.*)T", appt["start"]).group(1), "bId": bId}

if targetAppt is not None:
    # make the appointment
    res = session.get(f"{pantry}/storefront/appointment").text
    # ->  <appointment-calendar csrf-token="de93...Fk41Q"
    csrfTok = re.search(r'<appointment-calendar\s+csrf-token="(.*?)"', res).group(1)

    session.post(
        f"{pantry}/storefront/make_appointment",
        data={
            "csrfToken": csrfTok,
            "start": targetAppt["start"],
            "blockId": targetAppt["bId"],
            "visitType": 14,
            "location": 1,
            # "clonePreviousOrder": 0,
            # "selectedShopNow": 0
        },
    )


# ----- Final Status


finalStatus = list()
orders = get_registrations()  # refresh, considering new appointment

if targetAppt is None:
    finalStatus.append(">> Could not make appointment <<")

if len(orders) != 0:
    finalStatus.append("Current Registration:")
    for order in orders:
        today = datetime.today()
        status = "(old)" if order < today else "(new)"
        finalStatus.append(f"\t- {status} {order}")
else:
    finalStatus.append("No current appointment.")


finalStatus = "\n".join(finalStatus)
print(finalStatus)


def send_imessage(message, phone_number=None):
    if phone_number is None:
        if "phone_number" not in conf:
            return
        phone_number = conf["phone_number"]

    script = f"""
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                send "{message}" to buddy "{phone_number}" of targetService
            end tell
            """
    subprocess.run(["osascript", "-e", script])


send_imessage(finalStatus)
