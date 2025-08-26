import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix
from pyproj import Transformer
import io
import geopandas as gpd
import tempfile
import zipfile
import os

st.set_page_config(layout="wide")
# ---- Utility function to detect column names ----

cola, colb = st.columns([1, 15]) 

     
with cola:
        st.image("images.png", width=120)  

with colb:
        st.title("Spatial Proximity Calculator")
        st.write("")
        st.write("")
        st.write("")

col1, col2 = st.columns([10, 8])

with col1:


    def find_column(df, possible_names):
        for col in df.columns:
            if col.strip().lower() in [name.lower() for name in possible_names]:
                return col
        raise ValueError(f"None of {possible_names} found in columns {list(df.columns)}")

    # ---- Main Processing Function ----
    def process_file(uploaded_file, radii):
        df = pd.read_csv(uploaded_file)

        # Detect Easting/Northing columns
        easting_col = find_column(df, ["Easting", "east", "X"])
        northing_col = find_column(df, ["Northing", "north", "Y"])

        # Convert Easting/Northing → Lat/Lon (X, Y)
        transformer = Transformer.from_crs("EPSG:7856", "EPSG:4326", always_xy=True)
        lons, lats = transformer.transform(df[easting_col].values, df[northing_col].values)
        df["X"] = lons
        df["Y"] = lats

        # Compute distance matrix
        coords = df[[easting_col, northing_col]].values
        dist_matrix = distance_matrix(coords, coords)
        np.fill_diagonal(dist_matrix, np.inf)

        # Add buffer columns
        for r in radii:
            df[f"Within_{r}m"] = (dist_matrix <= r).any(axis=1).astype(int)

        return df


    # ---- Streamlit UI ----



    st.subheader("📍Easting/Northing to Lat–Lon")
    st.write("")
    st.write("Upload a CSV with Easting/Northing (GDA2020 MGA Zone 56) and get back Lat/Lon + buffer columns.")



    default_radii = [2, 3, 5, 10, 15, 20]

    # User input: select buffer distances
    user_radii = st.multiselect(
        "Select buffer distances (in meters) for catching nearby entires:",
        options=list(range(1, 201, 1)),  # Allow selection from 1m to 200m
        default=default_radii
    )
    st.write("")
    st.write("")
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            st.success("✅ File uploaded successfully!")
            result_df = process_file(uploaded_file, user_radii)

            st.subheader("Download Processed CSV file")
            st.dataframe(result_df.head(10))

            # Convert DataFrame to CSV for download
            output = io.StringIO()
          
            st.download_button(
                label="📥 Download Processed CSV file",
                data=output.getvalue(),
                file_name="Updated CSV with x/y and radius marked.csv",
                mime="text/csv"
            )
           result_df.to_csv(output, index=False)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
with col2:

    def convert_shapefile_to_geojson(uploaded_zip):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save uploaded zip to temp folder
            zip_path = os.path.join(tmpdir, "shapefile.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.read())

            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Find the .shp file
            shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
            if not shp_files:
                raise ValueError("No .shp file found in uploaded zip")
            shp_path = os.path.join(tmpdir, shp_files[0])

            # Read shapefile
            gdf = gpd.read_file(shp_path)

            # Reproject to WGS84 (EPSG:4326)
            gdf = gdf.to_crs(epsg=4326)

            # Export GeoJSON
            geojson_str = gdf.to_json()
            return geojson_str

    # ---- Streamlit UI for shapefile upload ----
    st.subheader("📂 Shapefile to GeoJSON Converter (WGS84)")
    st.write("")  
    uploaded_zip = st.file_uploader("Upload a zipped shapefile (.zip)", type=["zip"])

    if uploaded_zip is not None:
        try:
            geojson_data = convert_shapefile_to_geojson(uploaded_zip)

            # Provide download button
            st.download_button(
                label="📥 Download GeoJSON",
                data=geojson_data,
                file_name="output.geojson",
                mime="application/json"
            )
            st.success("✅ Shapefile successfully converted to WGS84 GeoJSON!")

        except Exception as e:
            st.error(f"⚠️ Error converting shapefile: {e}")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)




