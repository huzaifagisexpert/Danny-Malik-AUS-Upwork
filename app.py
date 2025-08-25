import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix
from pyproj import Transformer
import io

# ---- Utility function to detect column names ----
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

col1, col2 = st.columns([1, 5])

with col1:
    st.image("images.png", width=100)  

with col2:
    st.title("Spatial Proximity Calculator")

st.title("Easting/Northing to Lat–Lon")
st.write("Upload a CSV with Easting/Northing (GDA2020 MGA Zone 56) and get back Lat/Lon + buffer columns.")



default_radii = [2, 3, 5, 10, 15, 20]

# User input: select buffer distances
user_radii = st.multiselect(
    "Select buffer distances (in meters) for catching nearby entires:",
    options=list(range(1, 201, 1)),  # Allow selection from 1m to 200m
    default=default_radii
)
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        st.success("✅ File uploaded successfully!")
        result_df = process_file(uploaded_file, user_radii)

        st.subheader("Download Processed CSV file")
        st.dataframe(result_df.head(10))

        # Convert DataFrame to CSV for download
        output = io.StringIO()
        result_df.to_csv(output, index=False)
        st.download_button(
            label="📥 Download Processed CSV file",
            data=output.getvalue(),
            file_name="Updated CSV with x/y and radius marked.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")


hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

