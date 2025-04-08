import json
import re
import subprocess
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# ----- Init


conf = json.load(open("config.json"))
daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

if conf["target"]["day"] not in daysOfWeek:
    print("Invalid config.target.day, expected one of: " + ", ".join(daysOfWeek))
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


# ----- Appointmentization


pantry = "https://app.pantrysoft.com"

now = datetime.now()
start = datetime.now() - relativedelta(months=1)
end = start + relativedelta(months=2)

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

if targetAppt is None:
    print("New appointment not registered.")
else:
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


# ----- Current Appointment Status


res = session.get(f"{pantry}/storefront/order_summary").text
soup = BeautifulSoup(res, "html.parser")
summary = soup.find("summary-page")

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
    orders.append(apptDate)

finalStatus = list()
finalStatus.append("Currrent Registration:")

for order in orders:
    finalStatus.append(f"\t- {order}")

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
