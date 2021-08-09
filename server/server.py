from flask import Flask
from flask import request
import h3
import numpy as np
import pandas as pd
import webbrowser
import os
import folium
from folium import Map
import geopandas as gpd
import geopy
from geopy.geocoders import Nominatim
import pickle
from geopy.extra.rate_limiter import RateLimiter
locator = Nominatim(user_agent="myGeocoder")
rgeocode = RateLimiter(locator.reverse, min_delay_seconds=0.001)
app = Flask(__name__)
def save_obj(obj, name ):
    with open('cache/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('cache/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)
cache = load_obj("clusters")
@app.route("/reload")
def reload_cache():
    print("Starting reload....")
    data =  pd.read_csv("./data/bee_parsed_all.csv")
    data.dropna()
    data = data.loc[data["latitude"] <1000000]
    data = data.loc[data["longitude"] <1000000]
    h3_level = 11
    def lat_lng_to_h3(row):
        return h3.geo_to_h3(row['latitude'], row['longitude'], h3_level)
    data['h3'] = data.apply(lat_lng_to_h3, axis=1)
    h3_clusters = dict()

    for index, row in data.iterrows():
        key = row['h3']
        if key in h3_clusters:
            h3_clusters[key]["count"] += 1
        else:
            h3_clusters[key] = {"count": 1,
                                "geom": h3.h3_to_geo_boundary(key)}
    relevant_clusters = { key:value for (key,value) in h3_clusters.items() if value['count'] >= 1000}
    toskip = []
    filtered_geo = []
    filtered_geo_id = []
    print("Almost there")
    cluster_geo = [h3.h3_to_geo(h) for h in relevant_clusters.keys()]
    for idx,i in enumerate(cluster_geo):
        if idx in toskip:
            continue
        filtered_geo.append(list(relevant_clusters.values())[idx])
        filtered_geo_id.append(list(relevant_clusters.keys())[idx])
        for s,j in enumerate(cluster_geo):
            if abs(i[0] - j[0]) < 0.00059:
                toskip.append(s)
            if abs(i[0]-j[0]) < 0.00059:
                toskip.append(s)
    for idx, i in enumerate(filtered_geo_id):
        filtered_geo[idx]["attributes-dis"] = {}
        coordinates = " ".join(map(str,h3.h3_to_geo(i)))
        filtered_geo[idx]["attributes-dis"]["address"] = rgeocode(coordinates).raw
        print("hello")
        filtered_geo[idx]["attributes-dis"]["count"] = filtered_geo[idx]["count"]
        print(filtered_geo[idx]["count"])
    alldict = dict(zip(filtered_geo_id,filtered_geo))
    cache = alldict
    print("Saving....")
    save_obj(alldict,"clusters")
    print("Done!")
    return "Done!"
@app.route("/fetch")
def fetch():
    return cache
@app.route("/add/<id>", methods = ['POST'])
def add(id):
    print(request.form)
    for i in request.form.keys():
        cache[id]["attributes-dis"][i] = request.form[i]
    print(cache[id])
    save_obj(cache,"clusters")
    return cache[id]

app.run(host='0.0.0.0', port=3000)