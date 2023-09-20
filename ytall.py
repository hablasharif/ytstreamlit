import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import tempfile
import os
from datetime import datetime
import pyperclip

# Initialize Streamlit app
st.title("YouTube Channel Video Extractor")

# Authenticate with YouTube API using API Key
API_KEY = "AIzaSyCefmb_xpwSOyMsBOCOjuRSrCtAwbZI_bA"
  # Replace with your YouTube API Key
youtube_service = build("youtube", "v3", developerKey=API_KEY)

# Extract all channel videos (with pagination)
def extract_all_channel_videos(channel_id):
    videos = []
    next_page_token = None

    while True:
        request = youtube_service.search().list(
            channelId=channel_id,
            type="video",
            order="date",
            part="snippet",
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()
        videos.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    return videos

# Retrieve channel name from channel ID
def get_channel_name(channel_id):
    request = youtube_service.channels().list(
        part="snippet",
        id=channel_id,
    )
    response = request.execute()
    if "items" in response:
        return response["items"][0]["snippet"]["title"]
    return None

# Format date as "day month year, hour minute am/pm, day"
def format_date(date):
    datetime_obj = datetime.fromisoformat(date)
    formatted_date = datetime_obj.strftime("%d %B %Y, %I:%M %p, %A")
    return formatted_date

# Streamlit UI
channel_id = st.text_input("Enter YouTube Channel ID:")
if channel_id:
    channel_name = get_channel_name(channel_id)
    if channel_name:
        videos = extract_all_channel_videos(channel_id)
        if videos:
            st.header(f"Channel Videos for {channel_name}:")
            
            # Create a list to hold the data for the table
            table_data = []

            for idx, video in enumerate(videos):
                title = video["snippet"]["title"]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                upload_date = format_date(video["snippet"]["publishedAt"])
                thumbnail_url = video["snippet"]["thumbnails"]["default"]["url"]
                description = video["snippet"]["description"]
                
                # Add data for each video as a row
                table_data.append([title, video_url, upload_date, thumbnail_url, description])

            # Create a DataFrame from the data
            df = pd.DataFrame(table_data, columns=["Video Title", "URL", "Upload Date", "Thumbnail", "Description"])

            # Display the table
            st.write(df)

            # Get the current date and time
            current_datetime = datetime.now()
            formatted_current_date = current_datetime.strftime("%d %B %Y, %I:%M %p, %A")

            # Define filenames with the channel name, username, and date
            file_name_prefix = f"{channel_name}_{formatted_current_date}"

            xlsx_file_name = f"{file_name_prefix}_videos.xlsx"
            html_file_name = f"{file_name_prefix}_videos.html"

            # Create temporary directories for files
            temp_dir = tempfile.mkdtemp()
            xlsx_temp_file = os.path.join(temp_dir, xlsx_file_name)
            html_temp_file = os.path.join(temp_dir, html_file_name)

            # Write Excel and HTML files to temporary files
            with pd.ExcelWriter(xlsx_temp_file, engine="xlsxwriter", mode="w") as writer:
                df.to_excel(writer, sheet_name="Sheet1", index=False)

            # Create an HTML representation with custom CSS styling
            df_html = df.copy()
            df_html["Video Title"] = df_html["Video Title"].apply(lambda x: f'<a href="{x}" style="color: #0066cc;">{x}</a>')
            df_html["URL"] = df_html["URL"].apply(lambda x: f'<a href="{x}" style="color: #0066cc;">{x}</a>')
            df_html["Thumbnail"] = df_html["Thumbnail"].apply(lambda x: f'<a href="{x}"><img src="{x}" alt="Thumbnail" style="max-height:100px;"></a>')
            df_html = df_html.to_html(escape=False, index=False)
            html_content = f"""
            <html>
            <head>
                <style>
                    table {{
                        font-family: Arial, sans-serif;
                        border-collapse: collapse;
                        width: 100%;
                    }}

                    th, td {{
                        border: 1px solid #dddddd;
                        text-align: left;
                        padding: 8px;
                    }}

                    tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}

                    th {{
                        background-color: #4CAF50;
                        color: white;
                    }}
                </style>
            </head>
            <body>
            <h2>Channel Videos</h2>
            {df_html}
            </body>
            </html>
            """

            with open(html_temp_file, "w", encoding="utf-8") as html_file:
                html_file.write(html_content)

            # Download buttons using temporary files
            st.download_button(
                label="Download as XLSX",
                data=open(xlsx_temp_file, "rb").read(),
                file_name=xlsx_file_name,
                key="xlsx-download",
            )

            st.download_button(
                label="Download as HTML",
                data=open(html_temp_file, "rb").read(),
                file_name=html_file_name,
                key="html-download",
            )

            # Add one-click copy functionality for every column
            for column in df.columns:
                st.button(f"Copy {column}", key=f"copy-{column}")
                if st.button(f"Copy {column}"):
                    pyperclip.copy("\n".join(df[column].astype(str)))
                    st.success(f"{column} copied to clipboard!")

        else:
            st.warning("No videos found for the given channel ID.")
    else:
        st.warning("Channel name not found for the given channel ID.")
