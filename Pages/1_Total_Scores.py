import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.title("Total Scores")
data = pd.read_csv("./Data/Timeguessr_Stats_Final.csv")

data['Michael 5-day Average'] = data['Michael Total Score'].rolling(window=5).mean()
data['Sarah 5-day Average'] = data['Sarah Total Score'].rolling(window=5).mean()

data['Michael Cumulative Average'] = data['Michael Total Score'].expanding().mean()
data['Sarah Cumulative Average'] = data['Sarah Total Score'].expanding().mean()


fig = go.Figure()

# Line chart
fig.add_trace(go.Scatter(x=data['Date'], y=data['Michael Total Score'], 
                         mode='markers', name='Michael Total Score', 
                         marker=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=data['Date'], y=data['Michael Cumulative Average'],
                          mode='lines', name='Michael Cumulative Average',
                          line=dict(color='royalblue', dash='dash')))
fig.add_trace(go.Scatter(x=data['Date'], y=data['Sarah Total Score'],
                          mode='markers', name='Sarah Total Score',
                          marker=dict(color='darkred')))
fig.add_trace(go.Scatter(x=data['Date'], y=data['Sarah Cumulative Average'],
                          mode='lines', name='Sarah Cumulative Average',
                          line=dict(color='darkred', dash='dash')))

# Customize layout
fig.update_layout(
    title='Total Scores',
    xaxis_title='Date',
    yaxis_title='Total Score',
    template='plotly_white'
)

# Display in Streamlit
st.plotly_chart(fig)