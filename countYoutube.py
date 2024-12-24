import streamlit as st
from googleapiclient.discovery import build
import pandas as pd

# Đặt API Key của bạn
API_KEY = 'AIzaSyCUAU2jwAABITKdZuhWH--uIPJUfNByQMY'
video_url = "https://www.youtube.com/watch?v=YA74YE1bw1k"  #langson ^_^

        # Phát video tự động khi tải trang
st.video(video_url)
# Hàm lấy ID video từ một kênh
def get_channel_uploads(channel_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    request = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    )
    
    response = request.execute()
    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return uploads_playlist_id

# Hàm lấy thông tin video
def get_videos_from_playlist(playlist_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    videos = []
    next_page_token = None
    
    while True:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        
        response = request.execute()
        
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            publish_time = item['snippet']['publishedAt']  # Lấy thời gian tải lên
            videos.append((video_id, title, publish_time))
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return videos

# Hàm lấy thống kê video
def get_video_stats(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    request = youtube.videos().list(
        part='statistics',
        id=video_id
    )
    
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        stats = response['items'][0]['statistics']
        return {
            'viewCount': int(stats.get('viewCount', 0)),
            'likeCount': int(stats.get('likeCount', 0)),
        }
    return None

# Giao diện Streamlit
st.title("YouTube Channel Video Stats")
st.title("https://seostudio.tools/vi/youtube-channel-id  <---để lấy ID kênh")
channel_id = st.text_input("Nhập ID kênh YouTube:", "UCc_pE2B8AkSK-o1SRMZtL7g")

if st.button("Lấy Thống Kê Video"):
    if channel_id:
        uploads_playlist_id = get_channel_uploads(channel_id)
        videos = get_videos_from_playlist(uploads_playlist_id)
        
        video_stats_list = []
        
        for video_id, title, publish_time in videos:
            stats = get_video_stats(video_id)
            if stats:
                video_stats_list.append({
                    'Title': title,
                    'Video ID': video_id,
                    'Published At': publish_time,
                    'Views': stats['viewCount'],
                    'Likes': stats['likeCount']
                    #,
                    #'Video URL': f'https://www.youtube.com/watch?v={video_id}'  # Thêm link video
                })
# Đường dẫn video bạn muốn phát tự động

        # Tạo DataFrame và hiển thị
        if video_stats_list:
            df = pd.DataFrame(video_stats_list)

            # Sắp xếp theo lượt xem hoặc lượt thích
            sort_by = st.selectbox("Sắp xếp theo:", ["Lượt xem", "Lượt thích"])
            if sort_by == "Lượt xem":
                df = df.sort_values(by='Views', ascending=False)
            else:
                df = df.sort_values(by='Likes', ascending=False)

            # Đánh số thứ tự
            df.index = range(1, len(df) + 1)

            # Hiển thị bảng và thêm nút play
            st.dataframe(df[['Title', 'Video ID', 'Published At', 'Views', 'Likes']])
            st.write("Xem video:")
                
                # Tạo nút play cho từng video
            #for index, row in df.iterrows():
                    #st.write(f"{index}. **{row['Title']}**")
                    #st.video(row['Video URL'])  # Nhúng video
        else:
            st.error("Không tìm thấy video nào trong kênh.")
    else:
        st.warning("Vui lòng nhập ID kênh!")
        
        