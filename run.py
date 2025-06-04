from app import create_app

app = create_app() # Create the Flask app instance

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader =False) # use_reloader=False to prevent double execution of the script