from flask import Flask, jsonify, send_file
import json
import requests
import pandas as pd

app = Flask(__name__)

def fetch_data(category, search_term, site):
    with open('configs/competitor.json', 'r') as file:
        competitor = json.load(file)
    
    competitor = competitor.get(site)
    if not competitor:
        return {"error": "Competitor not found"}
    
    URL = competitor['store_api'] + search_term
    HEADERS = { 
        'Accept-Language': "en-US,en;q=0.9,hi;q=0.8",
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
        'Cookie': competitor['cookie']
    }
    
    response = requests.get(URL, headers=HEADERS)
    data = response.json()
    
    if data.get('items'):
        items = data.get('items')
        found_items = []
        for item in items:
            found_items.append({
                "Store": site,
                "Product Name": item.get('name', ''),
                "Category": category,
                "Price": item.get('base_price', None)
            })
        return found_items
    else:
        return {"error": "No items found"}

@app.route('/api/v1/getitem/<site>/<category>/<search_term>')
def get_item(site, category, search_term):
    items = fetch_data(category, search_term, site)
    return jsonify({"items": items})

@app.route('/api/v1/compare_prices/<category>/<search_term>')
def compare_prices(category, search_term):
    with open('configs/competitor.json', 'r') as file:
        competitor = json.load(file)

    data = []
    for site, competitor_data in competitor.items():
        items = fetch_data(category, search_term, site)
        if isinstance(items, list):
            for item in items:
                data.append({
                    "Store": site,
                    "Product Name": item.get('Product Name', ''),
                    "Category": item.get('Category', ''),
                    "Price": item.get('Price', None)
                })

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(data)

    # Pivot the DataFrame to get the desired structure
    df = df.pivot_table(index=['Product Name', 'Category'], columns='Store', values='Price', aggfunc='first')

    # Reset index to flatten the pivot table
    df.reset_index(inplace=True)

    # Save the DataFrame to an Excel file
    df.to_excel('compare_prices.xlsx', index=False)

    return send_file('compare_prices.xlsx')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
