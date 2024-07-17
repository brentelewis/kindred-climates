#pip install openmeteo-requests requests-cache retry-requests numpy pandas plotly geopy matplotlib tkinter

import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from geopy.geocoders import Nominatim
import plotly.graph_objs as go
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Necessary functions to get weather data
def get_lat_long(city, state):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(f"{city}, {state}")
    if location:
        return location.latitude, location.longitude
    else:
        return None, None
# get weather data from Open-Meteo
def get_weather_data(latitude, longitude, start_date, end_date):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
        "start_date": start_date,
        "end_date": end_date
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location
    response = responses[0]

    # Process daily data
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}
    daily_data["weather_code"] = daily_weather_code
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max

    daily_dataframe = pd.DataFrame(data=daily_data)
    return daily_dataframe

# Function to summarize the data
def summarize(data, city, start, end):
    # get interesting information about the weather for the time period
    avg_max_temp = round(sum(data["temperature_2m_max"]) / len(data), 1)
    avg_min_temp = round(sum(data["temperature_2m_min"]) / len(data), 1)
    highest_temp = round(max(data["temperature_2m_max"]), 1)
    lowest_temp = round(min(data["temperature_2m_min"]), 1)
    precip_sum = round(sum(data["precipitation_sum"]), 1)
    avg_wind_speed = round(sum(data["wind_speed_10m_max"]) / len(data), 1)
    max_wind_speed = round(max(data["wind_speed_10m_max"]), 1)

    num_clear_days = sum(1 for code in data["weather_code"] if code in [0, 1])
    num_cloudy_days = sum(1 for code in data["weather_code"] if code in [2, 3])
    num_foggy_days = sum(1 for code in data["weather_code"] if code in [45, 48])
    num_rainy_days = sum(1 for code in data["weather_code"] if code in [85, 86])
    num_snowy_days = sum(1 for code in data["weather_code"] if code in [71, 73, 75])
    num_stormy_days = sum(1 for code in data["weather_code"] if code in [95, 96, 99])

    # Prints weather data Summary
    print(f"{len(data)}-Day Weather Summary for {city} between {start} and {end}:"
          f"\nHighest temperature: {highest_temp}°F"
          f"\nLowest temperature: {lowest_temp}°F"
          f"\nAverage max temperature: {avg_max_temp}°F"
          f"\nAverage min temperature: {avg_min_temp}°F"
          f"\nTotal precipitation: {precip_sum} inches"
          f"\nAverage wind speed: {avg_wind_speed} mph"
          f"\nMaximum wind speed: {max_wind_speed} mph"
          f"\nNumber of clear days: {num_clear_days}"
          f"\nNumber of cloudy days: {num_cloudy_days}"
          f"\nNumber of foggy days: {num_foggy_days}"
          f"\nNumber of rainy days: {num_rainy_days}"
          f"\nNumber of snowy days: {num_snowy_days}"
          f"\nNumber of stormy days: {num_stormy_days}")

    return avg_max_temp, avg_min_temp, highest_temp, lowest_temp, precip_sum, avg_wind_speed, max_wind_speed, num_clear_days, num_cloudy_days, num_foggy_days, num_snowy_days, num_stormy_days, num_rainy_days

# Function to compare data and calculate similarity count
def compare_data(data1, data2):
    similarity_count_for_the_ages = 0

    if abs(sum(data1["temperature_2m_max"]) - sum(data2["temperature_2m_max"])) < 10:
        similarity_count_for_the_ages += 1

    if abs(sum(data1["temperature_2m_min"]) - sum(data2["temperature_2m_min"])) < 10:
        similarity_count_for_the_ages += 1

    if abs(max(data1["temperature_2m_max"]) - max(data2["temperature_2m_max"])) < 10:
        similarity_count_for_the_ages += 1

    if abs(min(data1["temperature_2m_min"]) - min(data2["temperature_2m_min"])) < 10:
        similarity_count_for_the_ages += 1

    if abs(sum(data1["precipitation_sum"]) - sum(data2["precipitation_sum"])) < 10:
        similarity_count_for_the_ages += 1

    if abs(sum(data1["wind_speed_10m_max"]) - sum(data2["wind_speed_10m_max"])) < 5:
        similarity_count_for_the_ages += 1

    if abs(max(data1["wind_speed_10m_max"]) - max(data2["wind_speed_10m_max"])) < 5:
        similarity_count_for_the_ages += 1

    if abs(sum(1 for code in data1["weather_code"] if code in [0, 1]) - sum(1 for code in data2["weather_code"] if code in [0, 1])) == 0:
        similarity_count_for_the_ages += 1

    if abs(sum(1 for code in data1["weather_code"] if code in [45, 48]) - sum(1 for code in data2["weather_code"] if code in [45, 48])) == 0:
        similarity_count_for_the_ages += 1

    if abs(sum(1 for code in data1["weather_code"] if code in [2, 3]) - sum(1 for code in data2["weather_code"] if code in [2, 3])) == 0:
        similarity_count_for_the_ages += 1

    if abs(sum(1 for code in data1["weather_code"] if code in [71, 73, 75]) - sum(1 for code in data2["weather_code"] if code in [71, 73, 75])) == 0:
        similarity_count_for_the_ages += 1

    if abs(sum(1 for code in data1["weather_code"] if code in [95, 96, 99]) - sum(1 for code in data2["weather_code"] if code in [95, 96, 99])) == 0:
        similarity_count_for_the_ages += 1

    return similarity_count_for_the_ages

# Function to create and display the graph
def create_graph(data1, data2, city1, city2):
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(8, 6))
    x_vals = list(range(1, len(data1["temperature_2m_max"]) + 1))
    axes[0].plot(x_vals, round(data1["temperature_2m_max"], 1), label=f'{city1} Max Temp', color='blue')
    axes[0].plot(x_vals, round(data1["temperature_2m_min"], 1), label=f'{city1} Min Temp', color='cyan')
    axes[1].plot(x_vals, round(data2["temperature_2m_max"], 1), label=f'{city2} Max Temp', color='red')
    axes[1].plot(x_vals, round(data2["temperature_2m_min"], 1), label=f'{city2} Min Temp', color='orange')

    axes[0].legend()
    axes[1].legend()
    axes[0].set_ylabel('Temperature (°F)')
    axes[1].set_ylabel('Temperature (°F)')
    axes[1].set_xlabel('Day')
    fig.suptitle(f'Max and Min Temperatures for {city1} and {city2}')

    return fig

# **MAIN**

def main():
    # get user input for these
    city1 = "Chattanooga"
    state1 = "Tennessee"
    city2 = "Austin"
    state2 = "Texas"
    start_date = "2024-04-04"
    end_date = "2024-04-13"

    # Get weather data for city1
    lat, lng = get_lat_long(city1, state1)
    weather1 = get_weather_data(lat, lng, start_date, end_date)

    # Get weather data for city2
    lat, lng = get_lat_long(city2, state2)
    weather2 = get_weather_data(lat, lng, start_date, end_date)

    # Summarize data
    summarize(weather1, city1, start_date, end_date)
    summarize(weather2, city2, start_date, end_date)

    # Create graph
    fig = create_graph(weather1, weather2, city1, city2)

    # Compare data
    similarity_count = compare_data(weather1, weather2)

    # Display results
    similarity_message = f"These two locations had similar weather patterns over the range selected. Similarity count = {similarity_count}" if similarity_count >= 10 else f"These two locations did not have similar weather patterns over the range selected. Similarity count = {similarity_count}/13"
    print(similarity_message)

    # Create tkinter window
    root = tk.Tk()
    root.title("Weather Comparison")

    # Create labels to display weather data
    data_label1 = tk.Label(root, text=f"Weather data for {city1}:")
    data_label1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    data_label2 = tk.Label(root, text=f"Weather data for {city2}:")
    data_label2.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Display weather data for city1
    weather_text1 = tk.Text(root, height=15, width=50)
    weather_text1.grid(row=1, column=0, padx=10, pady=10, sticky="w")
    weather_text1.insert(tk.END, f"Weather data for {city1}:\n\n")
    weather_text1.insert(tk.END, f"Highest temperature: {max(weather1['temperature_2m_max'])}°F\n")
    weather_text1.insert(tk.END, f"Lowest temperature: {min(weather1['temperature_2m_min'])}°F\n")
    weather_text1.insert(tk.END, f"Average max temperature: {round(sum(weather1['temperature_2m_max']) / len(weather1), 1)}°F\n")
    weather_text1.insert(tk.END, f"Average min temperature: {round(sum(weather1['temperature_2m_min']) / len(weather1), 1)}°F\n")
    weather_text1.insert(tk.END, f"Total precipitation: {round(sum(weather1['precipitation_sum']), 1)} inches\n")
    weather_text1.insert(tk.END, f"Average wind speed: {round(sum(weather1['wind_speed_10m_max']) / len(weather1), 1)} mph\n")
    weather_text1.insert(tk.END, f"Maximum wind speed: {round(max(weather1['wind_speed_10m_max']))} mph\n")
    weather_text1.insert(tk.END, f"Number of clear days: {sum(1 for code in weather1['weather_code'] if code in [0, 1])}\n")
    weather_text1.insert(tk.END, f"Number of cloudy days: {sum(1 for code in weather1['weather_code'] if code in [2, 3])}\n")
    weather_text1.insert(tk.END, f"Number of foggy days: {sum(1 for code in weather1['weather_code'] if code in [45, 48])}\n")
    weather_text1.insert(tk.END, f"Number of rainy days: {sum(1 for code in weather1['weather_code'] if code in [85, 86])}\n")
    weather_text1.insert(tk.END, f"Number of snowy days: {sum(1 for code in weather1['weather_code'] if code in [71, 73, 75])}\n")
    weather_text1.insert(tk.END, f"Number of stormy days: {sum(1 for code in weather1['weather_code'] if code in [95, 96, 99])}\n")

    # Display weather data for city2
    weather_text2 = tk.Text(root, height=15, width=50)
    weather_text2.grid(row=1, column=1, padx=10, pady=10, sticky="w")
    weather_text2.insert(tk.END, f"Weather data for {city2}:\n\n")
    weather_text2.insert(tk.END, f"Highest temperature: {max(weather2['temperature_2m_max'])}°F\n")
    weather_text2.insert(tk.END, f"Lowest temperature: {min(weather2['temperature_2m_min'])}°F\n")
    weather_text2.insert(tk.END, f"Average max temperature: {round(sum(weather2['temperature_2m_max']) / len(weather2), 1)}°F\n")
    weather_text2.insert(tk.END, f"Average min temperature: {round(sum(weather2['temperature_2m_min']) / len(weather2), 1)}°F\n")
    weather_text2.insert(tk.END, f"Total precipitation: {round(sum(weather2['precipitation_sum']), 1)} inches\n")
    weather_text2.insert(tk.END, f"Average wind speed: {round(sum(weather2['wind_speed_10m_max']) / len(weather2), 1)} mph\n")
    weather_text2.insert(tk.END, f"Maximum wind speed: {round(max(weather2['wind_speed_10m_max']))} mph\n")
    weather_text2.insert(tk.END, f"Number of clear days: {sum(1 for code in weather2['weather_code'] if code in [0, 1])}\n")
    weather_text2.insert(tk.END, f"Number of cloudy days: {sum(1 for code in weather2['weather_code'] if code in [2, 3])}\n")
    weather_text2.insert(tk.END, f"Number of foggy days: {sum(1 for code in weather2['weather_code'] if code in [45, 48])}\n")
    weather_text2.insert(tk.END, f"Number of rainy days: {sum(1 for code in weather2['weather_code'] if code in [85, 86])}\n")
    weather_text2.insert(tk.END, f"Number of snowy days: {sum(1 for code in weather2['weather_code'] if code in [71, 73, 75])}\n")
    weather_text2.insert(tk.END, f"Number of stormy days: {sum(1 for code in weather2['weather_code'] if code in [95, 96, 99])}\n")

    # Plot the graph
    fig_canvas = FigureCanvasTkAgg(fig, master=root)
    fig_canvas.draw()
    fig_canvas.get_tk_widget().grid(row=2, columnspan=2, padx=10, pady=10)

    # Display similarity count
    similarity_label = tk.Label(root, text=similarity_message)
    similarity_label.grid(row=3, columnspan=2, padx=10, pady=10)
    
    # Destroys program on close
    def on_closing():
        root.destroy()
        root.quit()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    
    tk.mainloop()

    

if __name__ == "__main__":
    main()
