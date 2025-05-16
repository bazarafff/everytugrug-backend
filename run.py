from dotenv import load_dotenv
load_dotenv()  # ✅ Load .env before anything else

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
