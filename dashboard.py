import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os
from babel.dates import format_date
from datetime import datetime
import altair as alt

sns.set(style='whitegrid')

# Cache for Total Users Calculation
@st.cache_data
def create_day_count_df (day_df):
    day_count_df = day_df.query('dteday >= "2011-01-01" and dteday < "2012-12-31"')
    return day_count_df

@st.cache_data
def create_total_reg_df (day_df):
    total_reg_df = day_df.groupby(by="dteday").agg({
        "registered": "sum"
    })
    total_reg_df = total_reg_df.reset_index()
    total_reg_df.rename(columns={
        "registered": "regist_sum"
    }, inplace=True)
    return total_reg_df

@st.cache_data
def create_total_casual_df (day_df):
    total_casual_df = day_df.groupby(by="dteday").agg({
        "casual": "sum"
    })
    total_casual_df = total_casual_df.reset_index()
    total_casual_df.rename(columns={
        "casual": "cas_sum"
    }, inplace=True)
    return total_casual_df

# Cache for Question Answering
@st.cache_data
def create_monthly_user_trends_df(day_df):
    monthly_user_trends_df = day_df.resample(rule='M', on='dteday').agg({
    "month": "max",
    "count_cr": "sum"
    })
    monthly_user_trends_df = monthly_user_trends_df.reset_index()
    monthly_user_trends_df.rename(columns={
        "month": "abc",
        "count_cr": "total"
    }, inplace=True)
    return monthly_user_trends_df

@st.cache_data
def create_daily_users_df (day_df):
    daily_users_df = day_df.groupby("a_week")["count_cr"].sum().reset_index()
    daily_users_df.rename(columns={"count_cr": "Total Users"}, inplace = True)
    max_day = daily_users_df.loc[daily_users_df["Total Users"].idxmax(), "a_week"]
    daily_users_df['highlight'] = daily_users_df['a_week'].apply(
        lambda x: 'Special Day' if x == max_day else 'Regular Day'
    )
    day_order = ['Sunday','Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    daily_users_df['a_week'] = pd.Categorical(daily_users_df['a_week'], categories=day_order, ordered=True)
    return daily_users_df

@st.cache_data
def create_weather_user_df (day_df):
    weather_user_df = day_df.groupby("weather_situation")["dteday"].count().reset_index()
    weather_user_df.rename(columns={"dteday": "total_weat"}, inplace=True)
    return weather_user_df

@st.cache_data
def create_hourly_user_df (hour_df):
    hourly_user_df = hour_df.groupby("hour").agg({
        "casual": "sum",
        "registered": "sum",
        "count_cr": "sum"
    })
    hourly_user_df = hourly_user_df.reset_index()
    hourly_user_df.rename(columns={
        "casual": "total_cas",
        "registered": "total_reg",
        "count_cr": "all_total"
    },inplace=True)
    return hourly_user_df

@st.cache_data
def create_rfm_df (day_df, recent_date):
    rfm_df = day_df.groupby(by="instant", as_index=False).agg({
        "dteday": "max",
        "count_cr": "sum"
    })
    rfm_df.columns =["num_instant", "max_dates", "frequency"]
    rfm_df["recency"] = rfm_df["max_dates"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_dates", axis=1, inplace=True)
    return rfm_df

# Cache for loading datasets
@st.cache_data
def load_data1():        
     base_dir = os.path.dirname(os.path.abspath(__file__))    
     file_path = os.path.join(base_dir, "dayz.csv")
     day_df = pd.read_csv(file_path)
     day_df["dteday"] = pd.to_datetime(day_df["dteday"], errors='coerce')
     return day_df     

@st.cache_data
def load_data2():        
     base_dir = os.path.dirname(os.path.abspath(__file__))    
     file_path = os.path.join(base_dir, "hourz.csv")
     hour_df = pd.read_csv(file_path)
     hour_df["dteday"] = pd.to_datetime(hour_df["dteday"], errors='coerce')
     return hour_df  

# Load datasets
day_df = load_data1()
hour_df = load_data2()

# Calculate recent_date from the full dataset (before applying the filter)
recent_date = day_df["dteday"].max()

# Streamlit sidebar for filtering by date range
min_date = day_df["dteday"].min().date()
max_date = day_df["dteday"].max().date()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/128/17677/17677548.png")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Convert start and end dates to datetime format
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter the dataset based on the selected date range
main_df = day_df[(day_df["dteday"] >= start_date) & 
                 (day_df["dteday"] <= end_date)]

# Create cached dataframes using the filtered data
monthly_user_trends_df = create_monthly_user_trends_df(day_df)
day_count_df = create_day_count_df(day_df)
total_reg_df = create_total_reg_df(day_df)
total_casual_df = create_total_casual_df(day_df)
daily_users_df = create_daily_users_df(day_df)
weather_user_df = create_weather_user_df(day_df)
hourly_user_df = create_hourly_user_df(hour_df)

# Create the RFM dataframe using the filtered data but with the recent_date based on the full dataset
rfm_df = create_rfm_df(day_df, recent_date)

# ===========================================================================================================
st.title('Welcome to :blue[Bicycle Rental] Dashboard! Let\'s get you cycling! :bike:')
# ===========================================================================================================

# Total Users Calculation
st.header('Total Users of Bicycle Rental', divider="red")

col1, col2, col3 = st.columns(3)

with col1:
    total_order = day_count_df.count_cr.sum()
    st.metric("Total All Users:", value=total_order)
with col2:
    total_regist = total_reg_df.regist_sum.sum()
    st.metric("Total Registered Users:", value=total_regist)
with col3:
    total_cas = total_casual_df.cas_sum.sum()
    st.metric("Total Casual Users:", value=total_cas)

#============================================================================================================
# 1. User Growth Trends Chart
st.header('User Growth Trends', divider="red")
st.line_chart(data=monthly_user_trends_df, x='dteday', y='total', use_container_width=True)

# Create the line Chart
chart = alt.Chart(monthly_user_trends_df).mark_line(interpolate='linear', strokeDash=[5, 5]).encode(
    x=alt.X('dteday:T', title=None), 
    y=alt.Y('total:Q', title=None)
).properties(
    width='container',  
    height=400          
)
# Create the points
points = alt.Chart(monthly_user_trends_df).mark_point(shape='triangle', size=50).encode(
   x=alt.X('dteday:T', title=None), 
   y=alt.Y('total:Q', title=None)   
)
# Combine the line chart and points
final_chart = chart + points

# Display the chart in Streamlit
st.altair_chart(final_chart, use_container_width=True)

#============================================================================================================
# 2. Total Daily Users
st.header('Total Daily Users', divider="red")
daily_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# Set up the figure for plotting
plt.figure(figsize=(10, 6))
plt.gcf().patch.set_facecolor('none')

# Create a colour palette for hue
palette = {
    'Regular Day': '#000080',  
    'Special Day': '#ff0000',  
}

# Create a bar plot for daily users
sns.barplot(
    x='a_week', 
    y='Total Users', 
    data=daily_users_df,
    hue='highlight',
    dodge=False,
    palette=palette
)
# Set the title and labels
plt.title('Daily Users', fontsize=16, fontweight='bold')
plt.xlabel('Days', fontsize=12, fontweight='bold')
plt.ylabel('Total Users', fontsize=12, fontweight='bold')

# Display the plot in Streamlit
st.pyplot(plt)

#============================================================================================================
#3. Percentage
st.header('Percentage of Users', divider="red")

# Calculate the percentage of users for each weather condition
weat_percent = (weather_user_df['total_weat'] / weather_user_df['total_weat'].sum()) * 100

# Set up the figure for the pie chart
plt.figure(figsize=(10, 5))  
plt.gcf().patch.set_facecolor('none')

# Create the pie chart
plt.pie(
    weat_percent,
    labels=weather_user_df['weather_situation'],
    autopct='%1.1f%%',
    colors=['#C62828', '#B0BEC5', '#4CAF50'],
    startangle=60, 
    textprops={'fontsize': 12, 'color': 'black'}
    )
# Set the title for the pie chart
plt.title('Percentage of Users by Weather Condition', color='black', fontsize=14, fontweight='bold')

# Display the pie chart in Streamlit
st.pyplot(plt)

#============================================================================================================
#4.Time of Increase in Bicycle Rentals
st.header('Bicycle Rental Trends by Hour', divider="red")

# Set up the figure size
plt.figure(figsize=(10, 5))

# Set the background color of the figure to transparent
plt.gcf().patch.set_facecolor('none')

# Create line plots for casual and registered users
sns.lineplot(x="hour", y="total_cas", data=hourly_user_df, label="Casual", color='blue')
sns.lineplot(x="hour", y="total_reg", data=hourly_user_df, label="Registered", color='red')

# Define the x-ticks for the hours of the day
x = np.arange(0, 24, 1)
plt.xticks(x)

# Add vertical lines to indicate significant hours (8 AM and 5 PM)
plt.axvline(x=8, color='black', linestyle='--')
plt.axvline(x=17, color='black', linestyle='--')

# Set legend properties
plt.legend(loc='upper right', fontsize=14)
plt.title("Total Users Per Hour", fontsize=16, fontweight='bold')
plt.xlabel("Hours", fontsize=12)

# Set the title and labels for the plot
plt.ylabel("Total Users", fontsize=12)

# Display the plot in Streamlit
st.pyplot(plt)
#============================================================================================================
# RFM Chart
st.header('Total Days', divider="red")

# Prepare the short version of num_instant
rfm_df["short_instant"] = rfm_df["num_instant"].astype(str).apply(lambda x: x[:8])

# Set up the figure and axes for plotting
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15,6))
color = "#000080"

# Create bar plot for Recency
sns.barplot(x="short_instant", y="recency",
            data=rfm_df.sort_values(by="recency", ascending=True).head(10), 
            color=color, ax=ax[0], legend=False)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Total Days")
ax[0].set_title("By Recency", loc="center", fontweight='bold', fontsize=20)
ax[0].tick_params(axis='x', labelsize=14)

# Create bar plot for Frequency
sns.barplot(y="frequency", x="num_instant",
            data=rfm_df.sort_values(by="frequency", ascending=False).head(10),
            color=color, ax=ax[1], legend=False)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Total Users")
ax[1].set_title("By Frequency", loc="center", fontweight='bold', fontsize=20)
ax[1].tick_params(axis='x', labelsize=14)

# Display the plots in Streamlit
st.pyplot(fig)

# Add a caption
st.caption('copyright © 2024 malifram')

if __file__ == "__main__":
    pass
