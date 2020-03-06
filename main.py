import darksky
from datetime import datetime
from flask import abort
import googlemaps
import os
import pytz
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse, Message

gmaps = googlemaps.Client(key=os.environ.get('GMAPS_API_KEY'))
URL = f"https://us-central1-{os.environ.get('GCP_PROJECT')}.cloudfunctions.net/twilio_weather_bot"


def twilio_weather_bot(request):
    validate(request)
    geocoding = get_geocoding(request.form['Body'])
    coordinates = geocoding['lat'], geocoding['lng']
    forecast = darksky.forecast(os.environ.get('DARKSKY_API_KEY'), *coordinates)
    report = generate_weather_report(geocoding, forecast)
    return reply_with(report)


def validate(request):
    validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

    request_valid = validator.validate(
        URL,
        request.form,
        request.headers.get('X-Twilio-Signature', ''))

    if not request_valid:
        abort(403)


def get_geocoding(message_body):
    address = message_body.split()[2:]
    result = gmaps.geocode(address)[0]
    return {
        'address': result['formatted_address'],
        'lat': result['geometry']['location']['lat'],
        'lng': result['geometry']['location']['lng'],
    }


def generate_weather_report(geocoding, forecast):
    current_forecast = forecast['currently']

    time = current_forecast['time']
    timezone = pytz.timezone(forecast['timezone'])

    summary = current_forecast.get('summary', 'No Summary Given')
    temperature = current_forecast.get('temperature', 'No Temperature Information Given')

    dt = datetime.fromtimestamp(time, tz=timezone)
    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    precipitation_report = get_precipitation_report(current_forecast)

    return (
        f"{geocoding['address'].upper()} WEATHER REPORT [{formatted_date}]:\n"
        f"Temperature: {temperature}\n"
        f"Precipitation: {precipitation_report}\n"
        f"Summary: {summary}"
    )


def get_precipitation_report(current_forecast):
    precip_probability = current_forecast.get('precipProbability', 0)
    precip_type = current_forecast.get('precipType')

    if precip_type is not None and precip_probability != 0:
        return f"{precip_probability * 100} of {precip_type}"

    return 'No Precipitation Information Given'


def reply_with(body):
    response = MessagingResponse()
    response.append(Message(body=body))
    return str(response)
