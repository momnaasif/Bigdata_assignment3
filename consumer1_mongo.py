import json
from kafka import KafkaConsumer
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import pandas as pd
from collections import deque
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import nltk
from pymongo import MongoClient

# Initialize NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Connect to MongoDB
def connect_to_mongodb():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['yourdatabase']  # Replace 'yourdatabase' with your database name
    return db

# Kafka Consumer Configuration
def create_consumer():
    return KafkaConsumer(
        'product_info_topic',             # Subscribe to the product_info topic
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',     # Read from the beginning of the topic
        enable_auto_commit=True,
        group_id='newest-my-group',       # A new group id to ensure starting from the earliest
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

# Tokenize and preprocess the title
def preprocess_title(title):
    # Tokenize the title
    tokens = word_tokenize(title.lower())

    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words and token not in string.punctuation]

    return tokens

# Process Data with Apriori Algorithm
def process_with_apriori(titles):
    if not titles:
        print("Title list is empty. Skipping processing.")
        return

    # Convert titles to list of lists
    title_list = [preprocess_title(title) for title in titles]

    # One-hot encode the titles
    te = TransactionEncoder()
    te_ary = te.fit(title_list).transform(title_list)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    # Find frequent itemsets
    frequent_itemsets = apriori(df, min_support=0.1, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)

    print("Frequent Itemsets:\n", frequent_itemsets)
    print("Association Rules:\n", rules)

    # Insert data into MongoDB
    db = connect_to_mongodb()
    collection = db['processed_data']
    data = frequent_itemsets.to_dict(orient='records')  # Convert DataFrame to dictionary
    collection.insert_many(data)
    print("Processed data inserted into MongoDB.")

# Main function to consume and process data
def consume_data(consumer):
    titles = deque(maxlen=10)  # Sliding window of titles

    print("Starting consumer...")
    try:
        for message in consumer:
            print("Full message received:", message)  # Debug: print entire message
            item = message.value

            title = item.get('title', '')
            if not title:
                print("No title found in the message or 'title' is empty.")
                continue  # If continuing is not desired, adjust logic here

            titles.append(title)
            print("Current window of titles:", list(titles))

            if len(titles) == 10:
                print(f"Processing current window of {len(titles)} titles")
                process_with_apriori(titles)

    except KeyboardInterrupt:
        print("Consumer stopped manually.")
    finally:
        consumer.close()

if _name_ == "_main_":
    consumer = create_consumer()
    consume_data(consumer)
