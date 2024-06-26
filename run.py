from calendar import monthrange
from datetime import timedelta
import os

import numpy as np

from dataset_handling import make_csv, get_updated_month_df, get_month_df
from dotenv import load_dotenv

import requests

from util import get_today_str, get_now_arg, get_ytd_inflation, get_last_day_of_last_month
from requests_oauthlib import OAuth1Session

load_dotenv()


class IPCMeli:
    def __init__(self):
        self.ytd_inflation = None
        self.last_day_of_month = None
        self.today_inflation = None
        self.month_inflation = None
        self.tweet_content = None

        self.consumer_key = os.environ.get("TW_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("TW_CONSUMER_SECRET")
        self.oauth_token = os.environ.get("TW_OAUTH_TOKEN")
        self.oauth_token_secret = os.environ.get("TW_OAUTH_TOKEN_SECRET")
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK")

    def run(self):
        print(f'Running at {get_now_arg().strftime("%Y-%m-%d %H:%M:%S")}')

        # Check if it's the last day of month and make tweet
        self.last_day_of_month = get_now_arg().day == monthrange(get_now_arg().year, get_now_arg().month)[1]
        self.make_tweet()

        # Make csv for next month
        if self.last_day_of_month:
            print("Making csv for next month")
            make_csv()

    def make_tweet(self):
        # Set Tweet's content
        self.set_tweet_content()

        payload = {"text": self.tweet_content}

        # Make the request
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.oauth_token,
            resource_owner_secret=self.oauth_token_secret,
        )

        # Making the request
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code == 201:
            print("Tweet generated successfully")
        else:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

    def set_tweet_content(self):
        self.tweet_content = ""
        self.calculate_inflation()

        if self.today_inflation > 0:
            emoji = "📈"
            month_message = "asciende al"
        elif self.today_inflation < 0:
            emoji = "📉"
            month_message = "desciende al"
        else:
            emoji = "👌"
            month_message = "se mantiene en"

        # Get tweet content
        self.tweet_content += f'🇦🇷 Inflación según Mercado Libre del {get_today_str()}\n\n'
        self.tweet_content += f'{emoji} Se registró una inflación del {self.today_inflation}%\n'

        # Check wheter it's the last day of month
        if self.last_day_of_month:
            self.tweet_content += f'🗓️ El mes cerró con una tasa de inflación del {self.month_inflation}%\n\n'
        else:
            self.tweet_content += f'🗓️ La tasa mensual {month_message} {self.month_inflation}%\n\n'

        # Add yearly inflation
        if get_now_arg().year >= 2024:
            self.tweet_content += f'🔺 La tasa anual acumulada es del {self.ytd_inflation}%\n'

    def calculate_inflation(self):

        # Get current date
        today_str = get_now_arg().strftime("%Y-%m-%d")

        # Get yesterday to compare with current date
        yesterday_str = (get_now_arg() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Get last analyzed date and compare to today
        last_analyzed_date = get_month_df().columns.astype(str).tolist()[-1]

        if today_str == last_analyzed_date:
            raise Exception("Date's inflation already calculated")
        elif yesterday_str > last_analyzed_date:
            self.send_discord_message(f"Analizando más de una fecha, del {last_analyzed_date} al {yesterday_str}")
            yesterday_str = last_analyzed_date

        # Get updated month df
        month_df = get_updated_month_df()

        # Get comparable df (remove deleted posts)
        month_df = month_df[month_df[today_str] > 0]

        # Compare prices
        month_df['diff'] = round(((month_df[today_str] - month_df[yesterday_str]) / month_df[yesterday_str]) * 100, 2)

        # Drop outliers
        month_df.loc[month_df['diff'].abs() > 500, 'diff'] = np.nan

        # Get today's percentage change
        self.today_inflation = round(month_df['diff'].mean(), 2)

        # Get price of first month's day (also has the date of last month's last date in the df)
        last_day_of_last_month = get_last_day_of_last_month().strftime("%Y-%m-%d")

        # Compare prices to month beggining
        month_df['diff_month'] = round(((month_df[today_str] - month_df[last_day_of_last_month]) /
                                        month_df[last_day_of_last_month]) * 100, 2)

        # Drop outliers
        month_df.loc[month_df['diff_month'].abs() > 500, 'diff_month'] = np.nan

        # Get month's percentage change
        self.month_inflation = round(month_df['diff_month'].mean(), 2)

        self.ytd_inflation = get_ytd_inflation(self.month_inflation)

    def send_discord_message(self, message_content: str):
        try:
            data = {
                'content': message_content
            }

            requests.post(self.webhook_url, json=data)
        except:
            pass


if __name__ == '__main__':
    IPCMeli().run()
