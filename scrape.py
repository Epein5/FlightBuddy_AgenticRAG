import requests
from bs4 import BeautifulSoup
import pandas as pd


def scrape():
        # URL of the webpage
    url = "https://www.tiairport.com.np/en-faq"

    # Output file name
    output_file = "DB/clean_scrape.txt"

    # Send a GET request to the URL
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all FAQ sections based on the button and accordion-content structure
        faqs = []
        buttons = soup.find_all('button', class_='accordion')
        contents = soup.find_all('div', class_='accordion-content')

        for button, content in zip(buttons, contents):
            question = button.text.strip()
            answer = content.get_text(strip=True)
            if question and answer:  # Ensure both question and answer are present
                faqs.append({'Question': question, 'Answer': answer})

        # Save the FAQs into a text file
        with open(output_file, 'w', encoding='utf-8') as file:
            for faq in faqs:
                file.write(f"Question: {faq['Question']}\n")
                file.write(f"Answer: {faq['Answer']}\n")
                # file.write("\n" + "="*80 + "\n\n")  # Separator for readability
                file.write("\n\n")

        print(f"FAQs have been saved to {output_file}")
    else:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")


def csv_data_creation():
    data = [
        ["Nepal Airlines", "Kathmandu", "New Delhi", "08:00", "09:30", "International", 0.01],
        ["Buddha Air", "Kathmandu", "Pokhara", "06:30", "07:15", "Domestic", 0.005],
        ["Yeti Airlines", "Kathmandu", "Lukla", "07:00", "07:30", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Bhadrapur", "09:00", "10:00", "Domestic", 0.015],
        ["Summit Air", "Kathmandu", "Jomsom", "06:45", "07:30", "Domestic", 0.03],
        ["Nepal Airlines", "Kathmandu", "Bangkok", "10:00", "13:30", "International", 0.01],
        ["Buddha Air", "Kathmandu", "Bhairahawa", "08:30", "09:20", "Domestic", 0.005],
        ["Yeti Airlines", "Kathmandu", "Janakpur", "09:15", "10:00", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Biratnagar", "11:00", "11:45", "Domestic", 0.015],
        ["Summit Air", "Kathmandu", "Simikot", "12:00", "13:00", "Domestic", 0.03],
        ["Nepal Airlines", "Kathmandu", "Kuala Lumpur", "23:00", "04:30", "International", 0.01],
        ["Buddha Air", "Pokhara", "Kathmandu", "10:30", "11:15", "Domestic", 0.005],
        ["Yeti Airlines", "Lukla", "Kathmandu", "08:00", "08:30", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Dhangadhi", "13:30", "15:00", "Domestic", 0.015],
        ["Summit Air", "Jomsom", "Kathmandu", "14:00", "14:45", "Domestic", 0.03],
        ["Nepal Airlines", "Kathmandu", "Doha", "18:00", "22:30", "International", 0.01],
        ["Buddha Air", "Kathmandu", "Simara", "07:30", "08:00", "Domestic", 0.005],
        ["Yeti Airlines", "Kathmandu", "Bharatpur", "08:15", "08:45", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Nepalgunj", "10:00", "11:00", "Domestic", 0.015],
        ["Summit Air", "Simikot", "Kathmandu", "11:30", "12:30", "Domestic", 0.03],
        ["Nepal Airlines", "Kathmandu", "Hong Kong", "20:00", "02:00", "International", 0.01],
        ["Buddha Air", "Kathmandu", "Tumlingtar", "06:00", "06:45", "Domestic", 0.005],
        ["Yeti Airlines", "Kathmandu", "Surkhet", "07:00", "08:00", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Rajbiraj", "09:30", "10:30", "Domestic", 0.015],
        ["Summit Air", "Kathmandu", "Rukum", "12:30", "13:30", "Domestic", 0.03],
        ["Nepal Airlines", "Kathmandu", "Singapore", "22:00", "04:30", "International", 0.01],
        ["Buddha Air", "Kathmandu", "Meghauli", "07:00", "07:30", "Domestic", 0.005],
        ["Yeti Airlines", "Kathmandu", "Taplejung", "08:45", "09:45", "Domestic", 0.02],
        ["Shree Airlines", "Kathmandu", "Gorkha", "10:45", "11:15", "Domestic", 0.015],
        ["Summit Air", "Kathmandu", "Dolpa", "12:45", "13:30", "Domestic", 0.03]
    ]

    # Create a DataFrame
    columns = [
        "Airline Name", 
        "From", 
        "To", 
        "Estimated Time of Take Off", 
        "Estimated Time of Arrival", 
        "Type", 
        "Death Rate (%)"
    ]
    df = pd.DataFrame(data, columns=columns)

    # Save to CSV
    file_path = "DB/Nepali_Airlines_Data.csv"
    df.to_csv(file_path, index=False)

    file_path

def csv_to_sqllitedb():
    import sqlite3
    import pandas as pd

    # Connect to the database
    conn = sqlite3.connect("DB/Nepali_Airlines_Data.db")

    # Load the CSV file into a DataFrame
    df = pd.read_csv("DB/Nepali_Airlines_Data.csv")

    # Save the DataFrame to the database
    df.to_sql("Nepali_Airlines_Data", conn, if_exists="replace", index=False)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# csv_to_sqllitedb()

def query_data():
    import sqlite3

    # Connect to the database
    conn = sqlite3.connect("DB/Nepali_Airlines_Data.db")

    # Query the database
    query = "SELECT * FROM Nepali_Airlines_Data WHERE `From` = \'Chitwan\' AND `To` = \'Lumbini\'"
    df = pd.read_sql_query(query, conn)

    # Display the results
    print(df)

    # Close the connection
    conn.close()

query_data()