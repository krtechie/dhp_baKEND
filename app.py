from flask import Flask, render_template, jsonify
import pandas as pd

app = Flask(__name__)

# Load single CSV file
def load_data():
    df = pd.read_csv('data/datacsv.csv')

    # Handle column headers (adjust if needed)
    if 'Tag' not in df.columns or 'Published DateTime' not in df.columns:
        df.columns = ['Tag', 'Published DateTime']  # fallback in case there's no header

    # Parse Published DateTime column properly
    df['Published DateTime'] = pd.to_datetime(df['Published DateTime'], utc=True, errors='coerce')
    df.dropna(subset=['Published DateTime'], inplace=True)

    # Extract Year and Month
    df['Year'] = df['Published DateTime'].dt.year
    df['Month'] = df['Published DateTime'].dt.to_period('M').astype(str)

    return df

data = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trend-by-year')
def trend_by_year():
    trend = data.groupby(['Year', 'Tag']).size().unstack(fill_value=0)
    return jsonify({
        "labels": list(trend.index),
        "datasets": [
            {
                "label": tag,
                "data": list(trend[tag]),
            } for tag in trend.columns
        ]
    })

@app.route('/api/tag-share-by-year')
def tag_share_by_year():
    result = {}
    for year in [2022, 2023, 2024]:
        tags = data[data['Year'] == year]['Tag'].value_counts().nlargest(10)
        result[str(year)] = {
            "labels": list(tags.index),
            "data": [int(v) for v in tags.values]
        }
    return jsonify(result)

@app.route('/api/wordcloud-data')
def wordcloud_data():
    tag_counts = data['Tag'].value_counts().nlargest(50)
    max_val = tag_counts.max()
    scaled = [[tag, int(count / max_val * 100)] for tag, count in tag_counts.items()]
    return jsonify(scaled)

@app.route('/api/grouped-top-tags')
def grouped_top_tags():
    # Count total tag frequency over all years
    top_tags = data['Tag'].value_counts().nlargest(10).index.tolist()

    grouped_data = {year: data[(data['Year'] == year) & (data['Tag'].isin(top_tags))]['Tag'].value_counts()
                    for year in [2022, 2023, 2024]}

    response = {
        "labels": top_tags,
        "datasets": []
    }

    for year in [2022, 2023, 2024]:
        year_counts = [int(grouped_data[year].get(tag, 0)) for tag in top_tags]
        response["datasets"].append({
            "label": str(year),
            "data": year_counts
        })

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)