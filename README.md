# Fresh_to_home
E-commerce backend with dynamic pricing, real-time inventory, and secure transactions — Python &amp; MySQL
A backend system for an e-commerce platform that sells fresh produce and groceries. Built with Python and MySQL, it handles product listings, dynamic pricing, real-time inventory, and secure user transaction
🚀 Features
🛒 Product Management — Add, update, and retrieve product listings
💰 Dynamic Pricing Engine — Automatically adjusts prices based on inventory levels and demand
📦 Real-time Inventory Tracking — Monitors stock and updates availability instantly
🔐 Secure Transactions — Parameterized queries and role-based access to protect user data
📊 Data Storage & Retrieval — Efficient MySQL database design for fast read/write operations

🛠️ Tech Stack
Layer	       : Technology
Language	   : Python 3.x
Database	   : MySQL
DB Connector : mysql-connector-python
Tools	       : Git, VS Code

📁 Project Structure

fresh-to-home/
│
├── db/
│   └── schema.sql          # Database schema and table definitions
│
├── modules/
│   ├── products.py         # Product listing and management
│   ├── pricing.py          # Dynamic pricing logic
│   ├── inventory.py        # Inventory tracking
│   └── transactions.py     # User transaction handling
│
├── config.py               # Database connection configuration
├── main.py                 # Entry point
└── README.md

⚙️ Getting Started
Prerequisites
Python 3.x installed
MySQL installed and running
mysql-connector-python library

Installation :
bash
# 1. Clone the repository
git clone https://github.com/prathvibk/fresh-to-home.git
cd fresh-to-home

# 2. Install dependencies
pip install mysql-connector-python

# 3. Set up the database
mysql -u root -p < db/schema.sql

# 4. Configure your database connection
# Edit config.py with your MySQL credentials

config.py:
python
DB_CONFIG = {
    "host": "localhost",
    "user": "your_mysql_username",
    "password": "your_mysql_password",
    "database": "fresh_to_home"
}

Run:
bash
python main.py

🗄️ Database Schema (Overview)
sql
-- Products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Transactions table
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT,
    total_price DECIMAL(10, 2),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


💡 How Dynamic Pricing Works
The pricing engine adjusts product prices automatically based on two factors:
Low stock → price increases (scarcity pricing)
High stock → price decreases (clearance pricing)
python
def calculate_dynamic_price(base_price, stock_quantity):
    if stock_quantity < 10:
        return base_price * 1.20   # 20% increase
    elif stock_quantity > 100:
        return base_price * 0.90   # 10% discount
    else:
        return base_price
🔐 Security
All database queries use parameterized statements to prevent SQL injection
User roles are validated before performing sensitive operations
Passwords and sensitive config are kept outside the codebase


📌 Future Improvements
 Add REST API layer using Flask
 Build a simple frontend with React
 Add user authentication (JWT)
 Deploy to AWS / Heroku
 Write unit tests with pytest







