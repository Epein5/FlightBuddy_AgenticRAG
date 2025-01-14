import requests
from bs4 import BeautifulSoup

# URL of the webpage
url = "https://www.tiairport.com.np/en-faq"

# Output file name
output_file = "scraped_faqs.txt"

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
            file.write("\n" + "="*80 + "\n\n")  # Separator for readability

    print(f"FAQs have been saved to {output_file}")
else:
    print(f"Failed to fetch the webpage. Status code: {response.status_code}")
