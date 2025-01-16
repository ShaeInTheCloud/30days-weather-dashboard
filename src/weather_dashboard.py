import os
import json
import boto3
import requests
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION'))

    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"Creating bucket {self.bucket_name}")
                try:
                    # Simpler creation for us-east-2
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"Successfully created bucket {self.bucket_name}")
                except ClientError as create_error:
                    print(f"Error creating bucket: {create_error}")

    def fetch_weather(self, city):
        """Fetch weather data from OpenWeather API"""
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def fetch_forecast(self, city):
        """Fetch weather forecast data from OpenWeather API"""
        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather forecast: {e}")
            return None

    def save_to_s3(self, weather_data, file_name):
        """Save weather data to S3 bucket"""
        if not weather_data:
            return False
            
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        try:
            weather_data['timestamp'] = timestamp
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"weather-data/{file_name}.json",
                Body=json.dumps(weather_data),
                ContentType='application/json'
            )
            print(f"Successfully saved data for {file_name} to S3")
            return True
        except ClientError as e:
            print(f"Error saving to S3: {e}")
            return False

    def visualize_weather(self, weather_data):
        """Visualize the weather data"""
        timestamps = [entry['dt_txt'] for entry in weather_data['list']]
        temps = [entry['main']['temp'] for entry in weather_data['list']]
        
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, temps, marker='o')
        plt.title('Temperature Forecast Over Time')
        plt.xlabel('Time')
        plt.ylabel('Temperature (°F)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

def main():
    dashboard = WeatherDashboard()
    
    # Create bucket if needed
    dashboard.create_bucket_if_not_exists()
    
    cities = ["Philadelphia", "Seattle", "New York"]
    
    for city in cities:
        print(f"\nFetching weather for {city}...")
        weather_data = dashboard.fetch_weather(city)
        forecast_data = dashboard.fetch_forecast(city)
        if weather_data and forecast_data:
            # Save current weather
            dashboard.save_to_s3(weather_data, f"{city}_current")

            # Save forecast data
            dashboard.save_to_s3(forecast_data, f"{city}_forecast")

            # Visualize forecast data
            dashboard.visualize_weather(forecast_data)

            print(f"Weather and forecast data for {city} saved to S3!")
        else:
            print(f"Failed to fetch weather data for {city}")

if __name__ == "__main__":
    main()
