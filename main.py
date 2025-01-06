import os
import string
import random
from datetime import datetime

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

#################################################
# 1. Flask app setup
#################################################
app = Flask(__name__)

# We expect a DATABASE_URL environment variable from Render (or fallback to local)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/mydb")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

#################################################
# 2. Define database model
#################################################
class Password(Base):
    __tablename__ = "passwords"
    
    id = Column(Integer, primary_key=True, index=True)
    password_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the table if it doesn't already exist
Base.metadata.create_all(bind=engine)

#################################################
# 3. Password generation function
#################################################
def generate_advanced_password(
    length=16,
    use_upper=True,
    use_lower=True,
    use_digits=True,
    use_punctuation=True
) -> str:
    """
    Generate an advanced password with the specified conditions.
    By default, 16 chars with upper, lower, digits, punctuation.
    """
    characters = ""
    if use_upper:
        characters += string.ascii_uppercase
    if use_lower:
        characters += string.ascii_lowercase
    if use_digits:
        characters += string.digits
    if use_punctuation:
        # You can tweak which punctuation chars you want
        characters += "!@#$%^&*()-_=+[]{}|;:,.<>/?"

    # Ensure at least 1 of each chosen character set
    password = []
    if use_upper:
        password.append(random.choice(string.ascii_uppercase))
    if use_lower:
        password.append(random.choice(string.ascii_lowercase))
    if use_digits:
        password.append(random.choice(string.digits))
    if use_punctuation:
        password.append(random.choice("!@#$%^&*()-_=+[]{}|;:,.<>/?"))

    # Fill the rest of the password length
    remaining_length = length - len(password)
    password += [random.choice(characters) for _ in range(remaining_length)]
    
    # Shuffle to prevent predictable pattern
    random.shuffle(password)
    
    return "".join(password)

#################################################
# 4. Endpoints
#################################################

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Advanced Password Maker!"

@app.route("/generate", methods=["POST"])
def generate_password():
    """
    POST /generate
    Body JSON (optional):
    {
      "length": 20,
      "use_upper": true,
      "use_lower": true,
      "use_digits": true,
      "use_punctuation": true
    }
    """
    data = request.get_json() if request.is_json else {}
    length = data.get("length", 16)
    use_upper = data.get("use_upper", True)
    use_lower = data.get("use_lower", True)
    use_digits = data.get("use_digits", True)
    use_punctuation = data.get("use_punctuation", True)
    
    # Generate the password
    new_password = generate_advanced_password(length, use_upper, use_lower, use_digits, use_punctuation)
    
    # Save to Postgres
    session = SessionLocal()
    password_entry = Password(password_value=new_password)
    session.add(password_entry)
    session.commit()
    session.refresh(password_entry)
    session.close()
    
    return jsonify({
        "message": "Password generated and stored successfully!",
        "generated_password": new_password
    }), 201

@app.route("/passwords", methods=["GET"])
def get_all_passwords():
    """
    GET /passwords
    Returns all passwords in the database (in real scenarios, you'd want authentication).
    """
    session = SessionLocal()
    all_passwords = session.query(Password).all()
    
    response = [
        {
            "id": pwd.id,
            "password_value": pwd.password_value,
            "created_at": pwd.created_at.isoformat()
        } for pwd in all_passwords
    ]
    session.close()
    
    return jsonify(response), 200

if __name__ == "__main__":
    # For local testing
    main.run(debug=True, host="0.0.0.0", port=5000)
