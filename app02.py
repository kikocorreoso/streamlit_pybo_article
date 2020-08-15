from typing import Union

import streamlit as st
import xarray as xr
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
    

# Código para mostrar en la aplicación Web
# Esta es la parte que explicaré con un poco más de detalle.
xarr = read_noaa("NOAA_V5_air_temperature_anomaly.nc")

st.title('#ShowYourStripes')
lon = st.slider(
    label="Longitud",
    min_value=0.0,
    max_value=360.0,
    value=0.0,
    step=0.5,
)
lat = st.slider(
    label="Latitud",
    min_value=-90.0,
    max_value=90.0,
    value=40.0,
    step=0.5,
)
if st.button("Pinta"):
    st.markdown(f"Longitud: {lon:.1f}")
    st.markdown(f"Latitud:  {lat:.1f}")
    fig, ts = plot_noaa(xarr, lon, lat)
    st.pyplot(fig)
    st.table(ts)
else:
    st.markdown(
        "Selecciona la localización usando los controles Y pulsa en "
        "el botón 'Pinta'."
    )
