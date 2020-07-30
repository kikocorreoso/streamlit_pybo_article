from typing import Union
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import streamlit as st
import xarray as xr
import pandas as pd
import seaborn as sns
import numpy as np
import folium

# Esto se explicó en:
# https://pybonacci.org/2020/01/20/pintando-las-bandas-del-calentamiento-warming-stripes-con-seaborn-y-matplotlib-en-python/
def read_noaa(filename: str) -> xr.Dataset:
    """Read the netCDF file downloaded using `download_noaa`.
 
    Parameters
    ----------
    filename : str
        The name of the file to read as `xarray.Dataset`
 
    Returns
    -------
    `xarray.Dataset`
    """
    return xr.open_dataset(filename)
 
# Esto se explicó en:
# https://pybonacci.org/2020/01/20/pintando-las-bandas-del-calentamiento-warming-stripes-con-seaborn-y-matplotlib-en-python/
def get_noaa_timeseries(
        xarr: xr.Dataset, 
        lon: Union[int, float], 
        lat: Union[int, float]
    ) -> xr.Dataset:
    """Get the annual temperature anomaly time series from NOAA data.
 
    Parameters
    ----------
    xarr : xr.Dataset
        `xarray.Dataset` containing the monthly anomalies.
    lon : Union[int, float]
        Longitude in decimal degrees. It will return the closest timeseries
        to this location.
    lat : Union[int, float]
        Latitude in decimal degrees. It will return the closest timeseries
        to this location.
 
    Returns
    -------
    `xarray.Dataset`.
    """
    data = xarr.sel(lon=lon, lat=lat, z=0, method='nearest')
    df = data.to_dataframe()['anom']
    ts = df * df.index.days_in_month
    ts = (     
        ts.groupby(pd.Grouper(freq='Y')).mean()      
        /      
        ts.groupby(pd.Grouper(freq='Y')).count() 
    )
    ts.name = "Anomalía de Temperatura"
    return ts[ts.index.year < 2020] # <- Modificado solo para usar años completos

# Esto se explicó en:
# https://pybonacci.org/2020/01/20/pintando-las-bandas-del-calentamiento-warming-stripes-con-seaborn-y-matplotlib-en-python/
def plot_noaa(
        xarr: xr.Dataset,
        lon: Union[int, float],
        lat: Union[int, float]
    ) -> None:
    lon = float(lon)
    lat = float(lat)
    ts = get_noaa_timeseries(xarr, lon, lat)
    # warming stripes adapted from https://towardsdatascience.com/climate-heatmaps-made-easy-6ec5be0be6ff
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(
        data=ts.values[np.newaxis,:],
        ax=ax,
        cmap='RdBu_r',
        cbar=False,
        vmin=ts.min(),
        vmax=ts.max(),
        center=0.,
        xticklabels=False, 
        yticklabels=False,
    )
    fig.tight_layout()
    #fig.savefig("warming_stripes.png")
    return fig, ts # <- Modificado para no guardar la imagen y devolver fig y ts
    


def create_geojson_grid(
    xnodes: Union[list, tuple, np.array], 
    ynodes: Union[list, tuple, np.array], 
    filename: str) -> None:
    """Function that creates polygons in a regular grid and creates
    a geojson file.

    Parameters
    ----------
    xnodes : array-like
        1D array like (`list`, `tuple`, `numpy.array`,...) with the
        longitude coordinates in decimal values.
    ynodes : array-like
        1D array like (`list`, `tuple`, `numpy.array`,...) with the
        latitude coordinates in decimal values.
    filename : str
        Output filename for the geojson file.

    Returns
    -------
    None.

    """
    with open(filename, 'w') as f:
        gj = '{"type":"FeatureCollection","features":['
        for x1, x2 in zip(xnodes[:-1], xnodes[1:]):
            x1 = int(x1)
            x2 = int(x2)
            xnode_half_width = x2 - x1
            for y1, y2 in zip(ynodes[:-1], ynodes[1:]):
                y1 = int(y1)
                y2 = int(y2)
                xnode_half_width = x2 - x1
                text = f"from ({x1},{y1}) to ({x2},{y2})"
                coords = [[[x1, y1], [x2, y1], [x2, y2], [x1, y2]]]
                pol = {
                    "type": "Feature",
                    "id": f"{text}",
                    "properties": {
                        "name": f"{text}",
                        "lon_center": x1 + xnode_half_width,
                        "lat_center": y1 + xnode_half_width,
                    },
                    "geometry":{"type":"Polygon","coordinates": coords}
                }
                gj += json.dumps(pol)
                gj += ','
        gj = gj[:-1] + ']}'
        f.write(gj)


def create_map(
        lon: Union[int, float],
        lat: Union[int, float],
        tile: str = "OpenStreetMap",
    ) -> None:
    mapa = folium.Map(location=(lat, lon), tiles=tile, zoom_start=5)
    filename = Path(".", "noaagrid.geojson")
    if not filename.is_file():
        xnodes = np.arange(-180, 185, 5)
        ynodes = np.arange(-90, 95, 5)
        create_geojson_grid(xnodes, ynodes, filename)
    folium.GeoJson(str(filename), name="grid").add_to(mapa)
    tooltip = "Posición elegida por el usuario"
    folium.Marker(
        [lat, lon], 
        popup=f"<i>Lon: {lon:.1f}, Lat: {lat:.1f}</i>", 
        tooltip=tooltip
    ).add_to(mapa)
    return mapa


# Código para mostrar en la aplicación Web
# Esta es la parte que explicaré con un poco más de detalle.
xarr = read_noaa("NOAA_V5_air_temperature_anomaly.nc")

st.title('#ShowYourStripes')
lon = st.sidebar.slider(
    label="Longitud",
    min_value=0.0,
    max_value=360.0,
    value=2.5,
    step=0.5,
)
lat = st.sidebar.slider(
    label="Latitud",
    min_value=-90.0,
    max_value=90.0,
    value=39.5,
    step=0.5,
)
tile = st.sidebar.selectbox(
    label="Mapa base",
    options=["OpenStreetMap", "Stamen Toner", "Stamen Terrain",
             "Stamen Watercolor", "CartoDB positron", "CartoDB dark_matter"],
    index=0,
)
if st.sidebar.button("Pinta"):
    st.markdown(f"Longitud: {lon:.1f}")
    st.markdown(f"Latitud:  {lat:.1f}")
    fig, ts = plot_noaa(xarr, 2.5, 39.5)
    mapa = create_map(lon, lat, tile=tile)
    st.pyplot(fig)
    st.markdown(mapa._repr_html_(), unsafe_allow_html=True)
    st.table(ts)
else:
    st.markdown(
        "Selecciona la localización usando los controles Y pulsa en "
        "el botón 'Pinta'."
    )
