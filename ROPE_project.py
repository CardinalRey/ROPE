import tkinter as tk
from tkinter import messagebox, simpledialog, Label, PhotoImage
import requests
from geopy.geocoders import Nominatim
from geopy import distance
import folium
import webbrowser
import os

OPENROUTE_API_KEY = '5b3ce3597851110001cf624895a7d6018f32450b8d73d29ad518cb17'
OPENROUTE_SERVICE_URL = 'https://api.openrouteservice.org/v2/directions/driving-car'

def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="route_optimizer")
    location = geolocator.geocode(city_name)
    return (location.latitude, location.longitude)

def get_distance(city1, city2):
    coords1 = get_coordinates(city1)
    coords2 = get_coordinates(city2)
    return distance.distance(coords1, coords2).km

def dijkstra_optimize_route(start_city, intermediate_cities, end_city):
    distances = {}
    for city in intermediate_cities:
        dist_to_start = get_distance(start_city, city)
        dist_to_end = get_distance(city, end_city)
        distances[city] = dist_to_start - dist_to_end

    sorted_cities = sorted(distances, key=distances.get)
    return [start_city] + sorted_cities + [end_city]

def get_route(start_coords, end_coords):
    params = {
        'api_key': OPENROUTE_API_KEY,
        'start': f'{start_coords[1]},{start_coords[0]}',
        'end': f'{end_coords[1]},{end_coords[0]}'
    }
    response = requests.get(OPENROUTE_SERVICE_URL, params=params)
    return response.json()

def offset_coordinates(coords, offset=0.0001):
    return [(lat + offset, lon + offset) for lat, lon in coords]

def add_route_to_map(map_object, route, color, midpoint_text, offset=0):
    route_coords = route['features'][0]['geometry']['coordinates']
    route_coords = [(coord[1], coord[0]) for coord in route_coords]
    if offset:
        route_coords = offset_coordinates(route_coords, offset)

    folium.PolyLine(route_coords, color=color, weight=2.5, opacity=1).add_to(map_object)

    mid_point_index = len(route_coords) // 2
    folium.map.Marker(
        route_coords[mid_point_index],
        icon=folium.DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html=f'<div style="font-size: 12pt; background: rgba(255, 255, 255, 0.6); border-radius: 5px; padding: 5px;">{midpoint_text}</div>',
        )
    ).add_to(map_object)

    return route_coords

def visualize_route(optimized_route):
    map_object = folium.Map(location=get_coordinates(optimized_route[0]), zoom_start=12)

    for city in optimized_route:
        folium.Marker(
            get_coordinates(city), 
            popup=folium.Popup(city, show=True),
            icon=folium.Icon(color='orange' if city in optimized_route[1:-1] else 'green' if city == optimized_route[0] else 'red')
        ).add_to(map_object)

    offset_value = 0.0001
    for i in range(len(optimized_route) - 1):
        start_city = optimized_route[i]
        end_city = optimized_route[i + 1]
        route = get_route(get_coordinates(start_city), get_coordinates(end_city))
        route_info = f'{start_city} to {end_city}: {route["features"][0]["properties"]["segments"][0]["distance"] / 1000:.2f} км, {route["features"][0]["properties"]["segments"][0]["duration"] / 60:.2f} хв'
        add_route_to_map(map_object, route, 'blue', route_info, offset=offset_value)
        offset_value += 0.0001

    return map_object

def main_gui():
    def on_submit():
        start_city = start_city_entry.get()
        end_city = end_city_entry.get()
        intermediate_cities = [city.strip() for city in intermediate_cities_entry.get().split(',') if city.strip()]

        if not start_city or not end_city:
            messagebox.showerror("Помилка", "Будь ласка, введіть місто відправлення та місто призначення.")
            return

        optimized_route = dijkstra_optimize_route(start_city, intermediate_cities, end_city)

        route_info = "Побудова маршруту:\n"
        for i in range(len(optimized_route) - 1):
            start = optimized_route[i]
            end = optimized_route[i + 1]
            dist = get_distance(start, end)
            route_info += f"{start} -> {end}: {dist:.2f} км\n"

        if messagebox.askyesno("Маршрут", route_info + "\nПобудувати маршрут на карті?"):
            map_object = visualize_route(optimized_route)
            map_file = 'route.html'
            map_object.save(map_file)
            webbrowser.open('file://' + os.path.realpath(map_file))

    root = tk.Tk()
    
    root.title("ROPE")
    root.attributes('-alpha', 0.8)
    root.geometry('500x350')
  
    background_image = PhotoImage(file="background.png")

    background_label = Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    tk.Label(root, text="Місто відправлення:").pack(pady=5)
    start_city_entry = tk.Entry(root)
    start_city_entry.config(bg='#ffffff', bd=5)
    start_city_entry.pack()

    tk.Label(root, text="Проміжні міста (розділені комами):").pack(pady=5)
    intermediate_cities_entry = tk.Entry(root)
    intermediate_cities_entry.config(bg='#ffffff', bd=5)
    intermediate_cities_entry.pack()

    tk.Label(root, text="Місто призначення:").pack(pady=5)
    end_city_entry = tk.Entry(root)
    end_city_entry.config(bg='#ffffff', bd=5)
    end_city_entry.pack()

    submit_button = tk.Button(root, text="Підтвердити", command=on_submit)
    submit_button.pack(pady=30)

    root.mainloop()

if __name__ == "__main__":
    main_gui()
