####   README   #### #### #### #### #### #### #### ####
# Run these scripts from the rateyildiz.com directory #
#### END README #### #### #### #### #### #### #### ####

import json
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('rateyildiz.db')
cursor = conn.cursor()

# Load the JSON data
with open('avesis_scraping/professors_info.json', 'r', encoding='utf-8') as file:
    professors_data = json.load(file)

# Prepare the SQL insert statement
insert_query = """
INSERT INTO professors (full_name, image_id, username, avesis_id, faculty_id, departments)
VALUES (?, ?, ?, ?, ?, ?)
"""

# Process and insert each professor's data
for professor in professors_data:
    full_name = professor['name']
    image_id = professor['image_id']
    username = professor['username']
    avesis_id = professor['user_id']
    faculty_id = professor['faculty_id']
    departments = ', '.join(professor['departments'])

    # Execute the insert statement
    try:
        cursor.execute(insert_query, (full_name, image_id, username, avesis_id, faculty_id, departments))
    except sqlite3.IntegrityError as e:
        print(f"Skipping duplicate entry for {full_name}: {e}")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Data import completed successfully!")
