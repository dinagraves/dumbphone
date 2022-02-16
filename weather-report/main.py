import json
import math
import os
import pytz
import urllib

from datetime import datetime, timezone
from twilio.rest import Client

API_KEY = os.environ["API_KEY"]
BASE_URL = "http://api.openweathermap.org/data/2.5/"
FROM_NUMBER = os.environ["TWILIO_NUMBER"]

##Todo: Update values below
HOME_LATLON = "lat=37.386051&lon=-122.083855"
TO_NUMBERS = ["+15555551234", "+15555551235"]
MY_TIMEZONE = pytz.timezone("US/Pacific")

def daily_update(request):
    req_url = (
        f"{BASE_URL}onecall?{HOME_LATLON}&appid={API_KEY}"
        "&units=imperial&exclude=minutely")
    req = urllib.request.Request(req_url)

    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print(data)

    daily_forecast = make_daily_msg(data.get("daily"))
    hourly_forecast = make_hourly_msg(data.get("hourly"))
    alerts = data.get("alerts")

    msg = ""
    if alerts:
        msg += "## ALERTS ##" f"{alerts}\n"
    
    msg += (
        "\n## DAILY FORECAST ##\n"
        f"{daily_forecast}\n"
    )

    if hourly_forecast:
        msg+= (
          "## HOURLY FORECAST ##\n"
          f"{hourly_forecast}\n"
          )

    twilio_responses = []

    for number in TO_NUMBERS:
        twilio_responses.append(send_msg(msg, number))
    return str(twilio_responses)


def make_hourly_msg(hours):
    # Hourly Forecast
    msg = ""

    # Using range because I only want 24 hours
    for x in range(0, 24):
        hour = hours[x]

        timestamp_utc = datetime.fromtimestamp(hour.get("dt"), timezone.utc)
        timestamp_tz = timestamp_utc.astimezone(MY_TIMEZONE)

        temp = hour.get("temp")
        weather = hour.get("weather")
        description = weather[0].get("description")

        # Only print hourly forecast if rain or snow is expected
        if "rain" in description or "snow" in description:
            hour_msg = f"{timestamp_tz.strftime('%a %-I%p')}: {math.floor(temp)}"
            hour_msg += f" {description}"

            msg += f"{hour_msg}\n"

    return msg


def make_daily_msg(daily):
    msg = ""

    # Today and tomorrow
    for x in range(0, 2):
        day = daily[x]

        timestamp = datetime.fromtimestamp(day.get("dt")).strftime("%A, %Y-%m-%d")
        temp = day.get("temp")
        weather = day.get("weather")

        day_msg = (
            f"Day: {timestamp}\n"
            f"High: {temp.get('max')}\n"
            f"Low: {temp.get('min')}\n"
            f"Weather: {weather[0].get('description')}\n"
        )

        # Rain and snow are reported in mm.
        # Convert to inches.
        rain = day.get("rain")
        if rain:
            rain_inches = round(float(rain)/25.4, 1)
            day_msg += f"Rain Inches: {rain_inches}\n"

        snow = day.get("snow")
        if snow:
            snow_inches = round(float(snow)/25.4, 1)
            day_msg += f"Snow Inches: {snow_inches}\n"
        msg += day_msg + "\n"

    return msg


def send_msg(msg, to_number):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)
    message = client.messages.create(body=msg, from_=FROM_NUMBER, to=to_number)
    print(message.sid)
    return message.sid
