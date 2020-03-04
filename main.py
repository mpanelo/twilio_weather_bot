import darksky
from datetime import datetime
from flask import abort
import googlemaps
import os
import pytz
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse, Message

gmaps = googlemaps.Client(key=os.environ.get('GMAPS_API_KEY'))


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
        request.url,
        request.form,
        request.headers.get('X-TWILIO-SIGNATURE', ''))

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

    summary = current_forecast['summary']
    precip_probability = current_forecast['precipProbability'] * 100
    precip_type = current_forecast['precipType']

    dt = datetime.fromtimestamp(time, tz=timezone)
    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"{geocoding['address'].upper()} WEATHER REPORT [{formatted_date}]:\n"
        f"Temperature: {current_forecast['temperature']}\n"
        f"Precipitation: {precip_probability}% of {precip_type}\n"
        f"Summary: {summary}"
    )


def reply_with(body):
    response = MessagingResponse()
    response.append(Message(body=body))
    return str(response)
