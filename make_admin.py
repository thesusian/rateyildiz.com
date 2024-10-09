import sqlite3
import sys

def make_user_admin(email):
    # Connect to the SQLite database
    conn = sqlite3.connect('rateyildiz.db')
    cursor = conn.cursor()

    try:
        # Update the user's admin status
        cursor.execute("""
            UPDATE users
            SET admin = 1
            WHERE gmail = ?
        """, (email,))

        # Commit the changes
        conn.commit()

        # Check if any row was affected
        if cursor.rowcount == 0:
            print(f"No user found with email: {email}")
        else:
            print(f"User {email} has been made an admin successfully!")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <user_email>")
        sys.exit(1)

    user_email = sys.argv[1]
    make_user_admin(user_email)
