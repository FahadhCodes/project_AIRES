from AIRE import app, db

if __name__ == "__main__":
    with app.app_context():
        # Import models so SQLAlchemy registers them before table creation
        from AIRE import models  # noqa

        print("Attempting to create database tables...")
        db.create_all()
        print("Database creation complete.")

    # Run Flask development server
    app.run(debug=True, host="0.0.0.0", port=5000)
