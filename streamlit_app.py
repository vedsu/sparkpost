import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import requests

#------------------------------------------------------------------
# Streamlit App
#------------------------------------------------------------------
st.set_page_config(
    page_title="Sparkpost API",
    page_icon=":bar_chart:",
    layout="centered",
)
st.title("#---Sparkpost Dashboard---#")
BASE_URL = "https://api.sparkpost.com"
campaigns = []
all_results = []
events = None
from_date_str = None
to_date_str = None
campaign = None
campaigns_options = []
API_KEY = None
API_KEY_OLD = os.getenv("SPARKPOST_API_KEY_OLD")
API_KEY_NEW = os.getenv("SPARKPOST_API_KEY_NEW")


# Options to Switch between Sparkpost New and Old Account
options_key = {
     0: "SPARKPOST_NEW_ACCOUNT",
     1: "SPARKPOST_OLD_ACCOUNT",
     
}

st.write("--------------------------------------------")
st.markdown("Sparkpost Account")


selection = st.segmented_control(
    "-------------",
    options=options_key.keys(),
    format_func=lambda option: options_key[option],
    selection_mode="single",
)

if selection  != None:

    if options_key[selection] == "SPARKPOST_OLD_ACCOUNT":
        API_KEY = API_KEY_OLD
        st.success("You have selected the Old Account")
    else:
        API_KEY = API_KEY_NEW
        st.success("You have selected the New Account")


# Checkbox for Metrics Options

# Headers for API call
headers = {
    "Authorization": API_KEY,
    "Accept": "application/json"
}


# API URL for events
base_url = f"{BASE_URL}/api/v1/events/message"

# API URL for campaigns
campaign_url = f"{BASE_URL}/api/v1/templates"

# Date Range
st.write("__________________")
st.markdown("Select the date range-")

col1, col2 = st.columns(2)
with col1:
        from_date = st.date_input(
            label = "From Date:",
            value = "today",
            min_value = None,
            max_value = None,
            format = "YYYY-MM-DD"
        )
        from_date_str = f"{from_date}T00:00"
        st.info(from_date_str)
with col2:
        to_date = st.date_input(
            label="To Date:",
            value= "today",
            min_value = None,
            max_value = None,
            format = "YYYY-MM-DD",
        )
        to_date_str = f"{to_date}T24:00"
        st.info(to_date_str)


# Events Options
st.write("_______________")
st.markdown("Select Events-")
options = [ "delivery", "injection", "bounce", "delay", "policy_rejection",
            "out_of_band", "open", "click", "generation_failure", "generation_rejection",
            "spam_complaint", "list_unsubscribe", "link_unsubscribe"]
events_options = st.pills("-----------", options, selection_mode = "multi", default = ["bounce"])
st.warning(events_options)
events = ",".join(events_options)

if selection  != None:
    # Checkbox for Campaigns
    st.write("")
    campaign_checkbox = st.checkbox("Choose Campaign-")
    if campaign_checkbox:
        
        
        # Params for Campaigns
        params_campaign = {
            "from": from_date_str,
            "to": to_date_str,
        }

        
        # API Call for Campaigns 
        try:

            response_campaign = requests.get(campaign_url, headers = headers)
            if response_campaign.status_code == 200:
                campaign_data = response_campaign.json()
                campaign_list = campaign_data["results"]
                df_campaign = pd.json_normalize(campaign_list)
                campaigns_options = df_campaign["id"].unique()

        except Exception as e:
            st.error(f"Error: {e}")
        
        campaign = st.selectbox(
            "Select template",
            options=campaigns_options,
            index=0,
        )
    st.write("")

    # Checkbox to get the sample data
    if st.toggle("Check", key="Checkbox"):
        
        # Params for Events
        params = {
        
            "events": events,
            "from": from_date_str,
            "to": to_date_str,
            "per_page": 10000,
            "templates": campaign,
            }

        try:
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data["results"])
                st.success(f"Total Count:{data["total_count"]}")
                if data["total_count"] == 0:
                    st.warning("No data found for the selected date range and events.")
                    
                
                else:
                    subjects = df["subject"].unique()
                    st.info(subjects)
                    st.dataframe(df.head(100))


                    all_results.extend(data["results"])

                    # Button to Load More Data for Pagination
                    if st.button("Load More Data", key="load_more_data"):
                        count = 1
                        while "links" in data and "next" in data["links"]:
                            st.toast(f"Page {count}  Loaded", icon = "🚨")
                            count += 1
                            next_url = BASE_URL + data["links"]["next"]
                            response = requests.get(next_url, headers=headers)
                            data = response.json()
                            all_results.extend(data["results"])

                        # Assume 'data' contains the API response
                        df = pd.json_normalize(all_results)

                        st.download_button(
                            label="Download Data",
                            data=df.to_csv(index=False).encode('utf-8'),
                            file_name='sparkpost_data.csv',
                            mime='text/csv',
                        )
            
        
        except Exception as e:
            st.error(f"Error: {e}")
