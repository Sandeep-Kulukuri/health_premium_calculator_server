from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask('health_care')
conn_str = 'mongodb+srv://<username>:<password>@<cluster>'
client = MongoClient(conn_str)

rate_card_collection = client['health_care_plan']['rate_card']


@app.route('/calculate_premium', methods=['POST'])
def get_expected_premium():
    data = request.json

    age_list = data.get('age_list', [])
    sum_insured = data.get('sum_insured', 0)
    city_tier = data.get('city_tier', '')
    is_double_tenure = data.get('tenure', 1) == 2

    if not age_list or not sum_insured or not city_tier:
        return jsonify({"error": "Incomplete data provided."}), 400

    rate_card_data = list(rate_card_collection.find({}))

    total_premium = 0
    individual_premiums = []

    for age in age_list:

        rate_card_entry = None
        for entry in rate_card_data:
            if 'age_range' in entry and 'tier' in entry and entry['age_range'] == str(age) and entry['tier'] == city_tier:
                rate_card_entry = entry
                break

        if rate_card_entry is None:
            age_entries = [entry for entry in rate_card_data if
                           'age_range' in entry and 'tier' in entry and entry['age_range'] > str(age) and entry['tier'] == city_tier]
            if age_entries:
                nearest_entry = min(age_entries, key=lambda x: int(x['age_range']))
                rate_card_entry = nearest_entry

        if rate_card_entry:
            base_premium = int(rate_card_entry.get(str(sum_insured), 0))

            if len(age_list) > 1 and 'age_range' in rate_card_entry and rate_card_entry['age_range'] != str(max(age_list)):
                base_premium = base_premium * 0.5
            if is_double_tenure:
                base_premium = base_premium * 2
            individual_premiums.append({"age": age, "premium": base_premium})
            total_premium += base_premium
        else:
            return jsonify({"error": f"No rate card entry found for age {age} and tier {city_tier}"})

    return jsonify({
        "total_premium": total_premium,
        "individual_premiums": individual_premiums
    })


# Configure CORS to allow requests from your React application's origin
cors = CORS(app, resources={r"/calculate_premium": {"origins": "*"}})


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
