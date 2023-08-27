import os
import json
import requests
import pandas as pd
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np
import time

def existence_check_file(coin_name, existing_coins):
    return coin_name in existing_coins

def search_coin(coin_name):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_name}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"\nAn error occurred while making the API request: {e}")
    return None

def add_coin(coin_name, existing_coins):
    if search_coin(coin_name):
        with open("coin_names.txt", "a") as file:
            file.write(coin_name + "\n")
        print(f"\nThe cryptocurrency '{coin_name}' has been added successfully.")
        existing_coins.append(coin_name)
    else:
        print(f"\nThe cryptocurrency '{coin_name}' does not exist.")

def display_crypto_prices(crypto_names):
    cg = CoinGeckoAPI()
    current_time = datetime.now()
    df = pd.DataFrame(columns=["Name", "Symbol", "Date", "Time", "Price (USD)"])

    for name in crypto_names:
        coin_data = cg.get_coin_by_id(name)
        if coin_data:
            price = coin_data["market_data"]["current_price"]["usd"]
            df.loc[len(df)] = [name, coin_data["symbol"], current_time.strftime("%Y-%m-%d"), current_time.strftime("%H:%M:%S"), price]

    df = df.sort_values("Name")

    print("\nCrypto Prices:")
    print(df)

    filename = "crypto_prices.csv"
    if not os.path.exists(filename):
        df.to_csv(filename, index=False)
    else:
        df.to_csv(filename, mode='a', header=False, index=False)
    print(f"\nData appended to {filename}")

def load_favorite_coins():
    try:
        with open("favorite_coins.json", "r") as file:
            favorite_coins = json.load(file)
    except FileNotFoundError:
        favorite_coins = {}

    return favorite_coins

def save_favorite_coins(favorite_coins):
    with open("favorite_coins.json", "w") as file:
        json.dump(favorite_coins, file)

def add_favorite_coin(coin_name, favorite_coins, existing_coins):
    if existence_check_file(coin_name, existing_coins):
        favorite_coins[coin_name] = True
        save_favorite_coins(favorite_coins)
        print(f"\nThe cryptocurrency '{coin_name}' has been added to the favorite list.")
    else:
        print(f"\nThe cryptocurrency '{coin_name}' does not exist in the cryptocurrency list.")

def remove_favorite_coin(coin_name, favorite_coins):
    if coin_name in favorite_coins:
        del favorite_coins[coin_name]
        save_favorite_coins(favorite_coins)
        print(f"\nThe cryptocurrency '{coin_name}' has been removed from the favorite list.")
    else:
        print(f"\nThe cryptocurrency '{coin_name}' is not in the favorite list.")

def display_favorite_coins(favorite_coins):
    print("\nFavorite Cryptocurrencies:")
    if favorite_coins:
        for coin in favorite_coins:
            print(coin)
    else:
        print("No cryptocurrencies in the favorite list.")

def extract_coin_data(coin_name):
    coin_data = pd.read_csv("crypto_prices.csv")
    coin_data = coin_data[coin_data["Name"] == coin_name]
    return coin_data

def plot_coin_prices(coin_data):
    # Convert "Date" and "Time" columns to datetime
    coin_data["Datetime"] = pd.to_datetime(coin_data["Date"] + " " + coin_data["Time"])

    # Sort the data by datetime
    coin_data.sort_values("Datetime", inplace=True)
    print(coin_data)
    # Convert data to NumPy arrays
    datetime_array = coin_data["Datetime"].to_numpy()
    price_array = coin_data["Price (USD)"].to_numpy()

    # Plot the coin prices
    plt.scatter(datetime_array, price_array, marker="o", color="blue", label="Price (USD)")
    plt.plot(datetime_array, price_array)

    # Set labels and title
    plt.xlabel("Datetime")
    plt.ylabel("Price (USD)")
    plt.title("Price of Cryptocurrency Over Time")

    # Rotate x-axis labels for better visibility
    plt.xticks(rotation=45)
    # Show the legend
    plt.legend()
    # Show the plot
    plt.show()

def get_daily_average_prices(name, days):
    url = f"https://api.coingecko.com/api/v3/coins/{name}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    retries = 3  # Number of retries
    wait_time = 5  # Wait time in seconds between retries

    for i in range(retries):
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                prices = data['prices']
                dates = [pd.Timestamp.fromtimestamp(price[0] / 1000).date() for price in prices]
                prices = [price[1] for price in prices]
                df = pd.DataFrame({"Date": dates, "Price": prices})
                df = df.groupby("Date").mean().reset_index()

                filename = "crypto_prices.csv"
                df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
                return df
        except (requests.RequestException, ValueError) as e:
            print(f"An error occurred while fetching data: {e}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print(f"Unable to fetch data for {name}. Please try again later.")
    return None


def plot_price_chart(df, name, ax):
    ax.step(df["Date"].to_numpy(), df["Price"].to_numpy())
    ax.scatter(df["Date"].to_numpy(), df["Price"].to_numpy())
    ax.set_title(f"{name} Daily Price Chart")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.tick_params(axis='x', rotation=45)
    # Set the date format for the x-axis
    date_format = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    ax.set_xticks(df["Date"].to_numpy())
    ax.set_xticklabels(df["Date"], rotation=45)


def calculate_daily_change(df):
    daily_returns = df["Price"].pct_change()
    return daily_returns.sum()

def find_best_currency(names, days):
    best_currency = None
    best_change = float("-inf")
    for name in names:
        df = get_daily_average_prices(name, days)
        change = calculate_daily_change(df)
        if change > best_change:
            best_change = change
            best_currency = name
    return best_currency, best_change

with open("coin_names.txt", "r") as file:
    existing_coins = [coin.strip() for coin in file.readlines()]

favorite_coins = load_favorite_coins()

while True:
    print("\nmenu : \n\
           1. Add Cryptocurrency\n\
           2. View Cryptocurrency Prices\n\
           3. Chart of changes in the price of a cryptocurrency\n\
           4. Favorite list\n\
           5. Checking the daily chart and comparing cryptocurrencies\n\
           6. Exit\n")

    choice = input("Please enter the operation number: ")

    if choice == "1":
        coin_name = input("\nEnter the name of the cryptocurrency: ")
        if existence_check_file(coin_name, existing_coins):
            print(f"\n{coin_name} has already been added to the list.")
        else:
            add_coin(coin_name, existing_coins)

    elif choice == "2":
        while True:
            print("\nSub Menu:")
            print("            1. View Cryptocurrency Prices")
            print("            2. Back")

            sub_choice = input("\nPlease enter your choice: ")

            if sub_choice == "1":
                if len(existing_coins) == 0:
                    print("\nNo cryptocurrencies added yet.")
                else:
                    for i, coin in enumerate(existing_coins, start=1):
                        print(f"           {i} - {coin}")

                    selected_indices = [int(i) - 1 for i in input("Please enter the numbers of cryptoes (separated with ','): ").split(",")]
                    selected_coins = [existing_coins[index] for index in selected_indices]
                    display_crypto_prices(selected_coins)

            elif sub_choice == "2":
                break

            else:
                print("Invalid choice!")

    elif choice == "3":
        for i, coin in enumerate(existing_coins, start=1):
            print(f"           {i} - {coin}")
        selected_coin = existing_coins[int(input("Please enter the numbers of crypto: "))-1]
        selected_coin_data = extract_coin_data(selected_coin)
        if not selected_coin_data.empty:
            plot_coin_prices(selected_coin_data)
        else:
            print(f"No data available for cryptocurrency '{selected_coin}'.")

    elif choice == "4":
        while True:
            print("\nOperations on Favorite list : \n\
                1. Add Favorite Cryptocurrency\n\
                2. Remove Favorite Cryptocurrency\n\
                3. View Favorite Cryptocurrencies\n\
                4. Back\n")

            sub_choice = input("Please enter the operation number: ")

            if sub_choice == "1":
                coin_name = input("\nEnter the name of the cryptocurrency: ")
                add_favorite_coin(coin_name, favorite_coins, existing_coins)

            elif sub_choice == "2":
                coin_name = input("\nEnter the name of the cryptocurrency: ")
                remove_favorite_coin(coin_name, favorite_coins)

            elif sub_choice == "3":
                display_favorite_coins(favorite_coins)

            elif sub_choice == "4":
                print("Back")
                break

            else:
                print("Invalid operation!")

    elif choice == "5":
        for i, coin in enumerate(existing_coins, start=1):
            print(f"           {i} - {coin}")
        selected_indices = [int(i) - 1 for i in input("Please enter the numbers of cryptoes (separated with ','): ").split(",")]
        selected_coins = [existing_coins[index] for index in selected_indices]
        days = int(input("Please enter the number of days: "))
        num_coins = len(selected_coins)
        num_rows = (num_coins + 1) // 2  
        num_cols = min(num_coins, 2)  
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 6 * num_rows))
        axes = np.ravel(axes)  
        for i, name in enumerate(selected_coins):
            df = get_daily_average_prices(name, days)
            if df is not None:
                ax = axes[i]
                ax.step(df["Date"].to_numpy(), df["Price"].to_numpy())
                ax.set_title(f"{name} Daily Price Chart")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price (USD)")
                ax.set_xticks(df["Date"].to_numpy())
                ax.set_xticklabels(df["Date"], rotation=45)
        plt.tight_layout()
        plt.show()

    elif choice == "6":
        print("Exit.")
        break

    else:
        print("Invalid operation!")
