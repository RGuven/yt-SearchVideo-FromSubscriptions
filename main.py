import os, json

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from loguru import logger

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class SearchVideoNameFromSubscriptions:
    def __init__(self, client_secrets_file) -> None:
        self.client_secrets_file = client_secrets_file

        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = client_secrets_file  # "YOUR_CLIENT_SECRET_FILE.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )

        credentials = flow.run_console()
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials
        )

    def get_all_subscriptions_of_mine(self):
        # Initialize pageToken to None
        pageToken = None
        all_subscriptions = []

        while True:
            request = self.youtube.subscriptions().list(
                part="snippet", mine=True, maxResults=50, pageToken=pageToken
            )
            response = request.execute()
            # Add items from the response to the all_subscriptions list
            all_subscriptions.extend(response["items"])
            # If there is a nextPageToken, use it in the next request
            # If not, break the loop
            if "nextPageToken" in response:
                pageToken = response["nextPageToken"]
            else:
                break

        # save the all_subscriptions
        save_json("all_subscriptions.json", {"all_subscriptions": all_subscriptions})

        return all_subscriptions

    def search_videos_of_a_channel(self, channel_id, channel_name):
        # Initialize pageToken to None
        pageToken = None
        all_videos_of_channel = []
        while True:
            request = self.youtube.search().list(
                part="id",
                channelId=channel_id,
                type="video",
                order="date",
                maxResults=50,
                pageToken=pageToken,
            )
            response = request.execute()
            # Add items from the response to the all_videos_of_channel list
            all_videos_of_channel.extend(response["items"])
            # If there is a nextPageToken, use it in the next request
            # If not, break the loop
            if "nextPageToken" in response:
                pageToken = response["nextPageToken"]
            else:
                break

        # save the all_videos_of_channel
        save_json(
            f"./Channels-All-Videos/all_videos_of_{channel_name}.json",
            {"all_videos_of_channel": all_videos_of_channel},
        )

        return all_videos_of_channel

    def get_video_title(self, video_id):
        # Make a request to the videos().list method
        request = self.youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        # Extract the title from the response
        video_title = response["items"][0]["snippet"]["title"]

        # convert all letters to lower
        video_title = video_title.lower()
        return video_title


if __name__ == "__main__":
    client_secrets_file = "sample_client_secret.json"
    search_name_service = SearchVideoNameFromSubscriptions(
        client_secrets_file=client_secrets_file
    )

    search_a_word_list = ["prompt", "prompt engineering", "Combat"]
    search_a_word_list = [word.lower() for word in search_a_word_list]
    search_result = []

    search_channel_counter = 1

    all_subscriptions = search_name_service.get_all_subscriptions_of_mine()
    for channel in all_subscriptions:
        if search_channel_counter == 0:
            break

        channel_id = channel["snippet"]["resourceId"]["channelId"]
        channel_name = channel["snippet"]["title"]

        logger.info(f"Searching On {channel_name} Channel")

        all_videos_of_channel = search_name_service.search_videos_of_a_channel(
            channel_id=channel_id, channel_name=channel_name
        )

        for video in all_videos_of_channel:
            video_id = video["id"]["videoId"]
            video_title = search_name_service.get_video_title(video_id=video_id)

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            for word in search_a_word_list:
                if word in video_title:
                    search_result.append(
                        {
                            "video_title": video_title,
                            "video_url": video_url,
                            "channel_name": channel_name,
                        }
                    )

                    logger.success(f"Succes Match 🚀 : {video_title}")
                else:
                    pass
                    # logger.error(f"No Match!! : {video_title}")

    save_json("search_result.json", {"search_result": search_result})
