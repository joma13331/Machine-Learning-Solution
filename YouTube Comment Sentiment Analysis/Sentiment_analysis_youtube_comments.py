# -*- coding: utf-8 -*-

# Imports for gettings Youtube Comments
from googleapiclient.discovery import build
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

# Imports for performing Sentiment Analysis
import tensorflow as tf
import tensorflow_text as text
from official.nlp import optimization
import numpy as np

# Imports for Graphically representing Sentiment Data on a Webpage
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px

# To obtain Youtube API key
key = os.environ.get("YOUTUBE_API_KEY")

# Function which removes Emojis in the comments
def deEmojify(text):
    regrex_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return regrex_pattern.sub(r'',text)

# To obtain channel Url for Youtube Channel
def get_c_url(channel_name):
    search_url = "https://www.youtube.com/c/{}/videos"
    search_url = search_url.format(channel_name)
    return search_url

# To obtain channel Url for Youtube User
def get_user_url(channel_name):
    search_url = "https://www.youtube.com/user/{}/videos"
    search_url = search_url.format(channel_name)
    return search_url

# Function to map score to Sentiment
def mapping(result):
    if result>=0.7:
        return "positive"
    if result>=0.3:
        return "neutral"
    
    return "negative"

#Function to obtain the top 200 comments from latest 30 videos of any Youtube channel
def obtain_dataframe(url):
    
    driver = webdriver.Chrome()
    driver.get(url)

    main = BeautifulSoup(driver.page_source, 'lxml')

    items = main.find_all('a', {'class':'yt-simple-endpoint style-scope ytd-grid-video-renderer'})

    titles=[]
    video_ids=[]
    for item in items:
        titles.append(item.text)
        video_id = item.get('href')[-11:]
        video_ids.append(video_id)
        
    
    with build('youtube', 'v3', developerKey = key) as service:
    
        rows = []
        for title, video_id in zip(titles,video_ids):
        
            request = service.commentThreads().list(part = 'snippet', videoId=video_id, maxResults=100, order="relevance", textFormat="plainText")
            response = request.execute()
        
            comment_items = response["items"]
            for item in comment_items:
                row = [title, item["snippet"]["topLevelComment"]["snippet"]["publishedAt"][:10], item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]]
                rows.append(row)
                
            if 'nextPageToken' in response:
                video_response = service.commentThreads().list(
                    part = 'snippet',
                    videoId = video_id,
                    pageToken = response["nextPageToken"],
                    maxResults=100, order="relevance", textFormat="plainText"
                ).execute()
        
                comment_items = video_response["items"]
    
                for item in comment_items:
                    row = [title, item["snippet"]["topLevelComment"]["snippet"]["publishedAt"][:10], item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]]
                    rows.append(row)    
                
    for row in rows:
        row[2] = deEmojify(row[2])
        
    dataframe = pd.DataFrame(rows, columns=["Video Title", "Published At Date", "Comment"])
    return dataframe.dropna(axis=0)

# Function to Obtain Sentiments from the comments Dataframe Using Tensorflow
def obtain_dataframe_with_sentiment(dataframe):
    
    dataset = tf.convert_to_tensor(dataframe["Comment"], dtype=tf.string)

    sentiment_model = tf.keras.models.load_model("bert_sentiment_140_saved_model")

    results = sentiment_model.predict(dataset)
    results = np.squeeze(results, axis=-1)

    vfunc = np.vectorize(mapping)
    sentiment_result = vfunc(results)
    dataframe["Sentiment"] = sentiment_result
    
    return dataframe

# Function to obtain dataframe used in dash 
def data_Processing_for_dash_for_channels(channel_name):
    df = obtain_dataframe(get_c_url(channel_name))
    df = obtain_dataframe_with_sentiment(df)
    df.to_csv("youtube_{}.csv".format(channel_name))
    return df

# Function to obtain dataframe used in dash 
def data_Processing_for_dash_for_users(channel_name):
    df = obtain_dataframe(get_user_url(channel_name))
    df = obtain_dataframe_with_sentiment(df)
    df.to_csv("youtube_{}.csv".format(channel_name))
    return df


key = os.environ.get("YOUTUBE_API_KEY")

load_from_csv = False
count = 0
if(load_from_csv == True | count!=0):
    df_CNN = pd.read_csv("youtube_CNN.csv")
    df_PowerfulJRE = pd.read_csv("youtube_PowerfulJRE.csv")
    df_BenShapiro = pd.read_csv("youtube_BenShapiro.csv")
else:
    df_CNN = data_Processing_for_dash_for_users("CNN")
    df_PowerfulJRE = data_Processing_for_dash_for_users("PowerfulJRE")
    df_BenShapiro = data_Processing_for_dash_for_channels("BenShapiro")
    count+=1

app = dash.Dash(__name__)

fig = px.histogram(df_CNN, x = "Sentiment", facet_col="Video Title", title= "Hover over the histograms for more information", color="Sentiment")

for anno in fig['layout']['annotations']:
    anno['text']=''

app.layout = html.Div(children = [
    html.H1(children = "Youtube Sentiment Analysis"),
    
    html.Div(children='''
        This Webpage represents graphically the Sentiments from the youtube comment section
    '''),
    
    html.Br(),
    
    html.Div(children = [
        html.Div(children=[
            html.Label('Channel Name'),
        
        dcc.RadioItems(id = "channel_name", labelStyle={'display': 'block'},options = [
            {'label':'CNN', 'value':'CNN'},
            {'label':"Joe Rogan Experience", 'value':'PowerfulJRE'},
            {'label':"Ben Shapiro", 'value':"Ben Shapiro"}],
            value='CNN')], style={'padding': 10, 'flex': 1}),
        
        html.Div(children =[html.Label('Video Title'),
                            dcc.Dropdown(id ='video_titles')], style={'padding': 10, 'flex': 1})
        
        ], style={'display': 'flex', 'flex-direction': 'row'})
        ,
    
    dcc.Graph(
        id='simple_histogram',
        figure=fig
    )
    
    
        ]
    )
             
@app.callback(
    Output('video_titles', 'options'),
    Input('channel_name', 'value')
   )
def set_video_options(channel_name):
    if channel_name == 'CNN':
        return [{'label':i, 'value':i} for i in df_CNN['Video Title'].unique()]
    
    if channel_name == 'PowerfulJRE':
        return [{'label':i, 'value':i} for i in df_PowerfulJRE['Video Title'].unique()] 

    return [{'label':i, 'value':i} for i in df_BenShapiro['Video Title'].unique()]  


@app.callback(
    Output('simple_histogram', 'figure'),
    Input('video_titles', 'value'),
    Input('channel_name', 'value')
    ) 
def set_histogram(video_title, channel_name):
    if channel_name == 'CNN':
        df = df_CNN[df_CNN['Video Title']==video_title]
        if video_title == None:
            fig = px.histogram(df_CNN, x = "Sentiment", facet_col="Video Title", title= "Hover over the histograms for more information", color="Sentiment")
            for anno in fig['layout']['annotations']:
                anno['text']=''
            return fig
            
    elif channel_name == 'PowerfulJRE':
        df = df_PowerfulJRE[df_PowerfulJRE['Video Title'] == video_title]
        if video_title == None:
            fig = px.histogram(df_PowerfulJRE, x = "Sentiment", facet_col="Video Title", title= "Hover over the histograms for more information", color="Sentiment")
            for anno in fig['layout']['annotations']:
                anno['text']=''
            return fig
    else: 
        df = df_BenShapiro[df_BenShapiro['Video Title'] == video_title]
        if video_title == None:
            fig = px.histogram(df_BenShapiro, x = "Sentiment", facet_col="Video Title", title= "Hover over the histograms for more information", color="Sentiment")
            for anno in fig['layout']['annotations']:
                anno['text']=''
            return fig
        
    fig = px.histogram(df, x = "Sentiment",title= "Channel Name: {}, Video Title: {}".format(channel_name, video_title), color="Sentiment")
    
    
        
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
    
    
