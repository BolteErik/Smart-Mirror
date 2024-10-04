from flask import Flask, render_template, request
from datetime import datetime
import requests
import ephem
import pytz
import base64

app = Flask('app')

astronomyID = 'eaa4af6c-0bb5-47b4-8479-117b48ef01ed'
astronomySecret = '75f7ace39091b4b99d2659cf153abb2db2f4e458ef0627aea6f77a32d68234b5a59daee6b39fe78df450e181522a5a8cebd318763e3aec77a289ce0097cc1ac633666791f37d20e7d261c8c42abddc65ba00058ca17825d25f4966ab2093dbcecd57a48d191c90488d45dc49ed26cc7b'

userpass = "astronomyID:astronomySecret"
authString = base64.b64encode(userpass.encode()).decode()

news_api = "662b6b61a90c4a228c60bba8cb48e661"
wetkey = "ed689a5f50674e89ab35723edd06c549"
weather_url = 'http://api.openweathermap.org/data/2.5/weather'
forecast_url = 'http://api.openweathermap.org/data/2.5/forecast'
time_zone = "Europe/Ljubljana"


def calcMoon():
  moon = ephem.Moon()
  date = ephem.now()
  moon.compute(date)
  current_phase = moon.phase / 100
  yesterday = ephem.Date(date) - 1
  moon.compute(yesterday)
  previous_phase = moon.phase / 100
  moonImages = {
      'New Moon': 'newMoon.PNG',
      'Waxing Crescent': 'waxCrescent.PNG',
      'First Quarter': 'firstQ.PNG',
      'Waxing Gibbous': 'waxGib.PNG',
      'Full Moon': 'fullMoon.PNG',
      'Waning Gibbous': 'wanGib.PNG',
      'Last Quarter': 'secondQ.PNG',
      'Waning Crescent': 'wanCrescent.PNG',
  }
  if 0.0 <= current_phase < 0.001:
    return moonImages["New Moon"]
  elif 0.001 <= current_phase <= 0.499:
    if current_phase < previous_phase:
      return moonImages['Waning Crescent']
    else:
      return moonImages["Waxing Crescent"]
  elif current_phase == 0.5:
    if current_phase < previous_phase:
      return moonImages["Last Quarter"]
    else:
      return moonImages["First Quarter"]
  elif 0.51 <= current_phase <= 0.99:
    if current_phase < previous_phase:
      return moonImages['Waning Gibbous']
    else:
      return moonImages['Waxing Gibbous']
  elif current_phase >= 0.99:
    return moonImages['Full Moon']
  else:
    return 'Unknown phase'

def getTemp():
  city_name = 'Jesenice'
  country_code = 'SI'
  params = {'q': f'{city_name},{country_code}', 'appid': wetkey, 'units': 'metric'}
  response = requests.get(weather_url, params=params)
  weather_data = response.json()
  if response.status_code == 200:
    temperature = weather_data['main']['temp']
    return temperature
  else:
    return None

def getWeather(timestamp, timezone):
  utc_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
  utc_time = pytz.utc.localize(utc_time)
  local_timezone = pytz.timezone(timezone)
  local_time = utc_time.astimezone(local_timezone)
  day_of_week = local_time.strftime('%A')
  time = local_time.strftime('%H:%M')    
  date = local_time.strftime('%d %b')
  return f'{day_of_week}, {time}, {date}'

@app.route('/')
def hello_world():
  moonPhase = calcMoon()
  temp = getTemp()
  quote = requests.get('https://zenquotes.io/api/random').json()[0]['q']
  return render_template('home.html', phase = moonPhase, temperature = temp, quote = quote)

@app.route('/get_news')  
def get_news():
  arc = request.args["arc"]
  newsUrl = f'https://newsapi.org/v2/everything?sources=fox-news&language=en&apiKey={news_api}'
  response = requests.get(newsUrl).json()
  articles = response['articles'] if 'articles' in response else []
  relevant = articles[int(arc)]
  return relevant    

@app.route('/get_time')
def get_time():
  current_time = datetime.now(pytz.timezone(time_zone)).strftime('%H:%M')
  return current_time

@app.route('/teeth_timer')
def teeth_timer():
  temp = getTemp()
  return render_template('teethTimer.html', temperature = temp)

@app.route('/weather_forecast')
def weather_forecast():
  city = 'Jesenice'
  country_code = 'SI'
  params = {
    'q' : f'{city},{country_code}',
    'appid' : wetkey,
    'units' : 'metric',
    'cnt' : 7
  }
  response = requests.get(forecast_url, params = params)
  weather_data = response.json()
  forecast = weather_data['list']
  for day in forecast:
    day['dt_txt'] = getWeather(day['dt_txt'], time_zone)
  return render_template('forecast.html', forecast = forecast)
  

app.run(host='0.0.0.0', port=8080)