import requests

def get_bist_stocks():
    # IsYatirim API for all stocks
    url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseSelect"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        stocks = [item.get('value') for item in data.get('value', []) if item.get('value') and len(item.get('value')) in [4, 5]]
        print(f"Found {len(stocks)} stocks. Sample: {stocks[:10]}")
    except Exception as e:
        print("Error fetching from IsYatirim:", e)

get_bist_stocks()
