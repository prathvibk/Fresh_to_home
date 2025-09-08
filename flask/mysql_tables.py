import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'prathvi@123',
    'database': 'salmon_fish'
}

def create_tables():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # SQL query to create the 'admin' table if it doesn't exist
        create_admin_table_query = """
        CREATE TABLE IF NOT EXISTS admin (
            a_id VARCHAR(50) PRIMARY KEY,
            a_email VARCHAR(50) NOT NULL,
            a_password VARCHAR(255) NOT NULL
        )
        """

        # Create Seller Table
        create_seller_table_query = """
        CREATE TABLE IF NOT EXISTS seller (
            seller_id INT PRIMARY KEY AUTO_INCREMENT,
            s_name VARCHAR(50) NOT NULL,
            s_email VARCHAR(50) NOT NULL UNIQUE,
            s_password VARCHAR(50) NOT NULL,
            s_phone VARCHAR(15) NOT NULL,
            s_address TEXT NOT NULL
        ) AUTO_INCREMENT = 1001
        """

        # Create Product Table
        create_product_table_query = """
        CREATE TABLE IF NOT EXISTS m_product (
            product_id INT PRIMARY KEY AUTO_INCREMENT,
            p_name VARCHAR(50) NOT NULL,
            p_image VARCHAR(100),
            p_remark TEXT
        ) AUTO_INCREMENT = 2001
        """


        # Create Seller Product Table
        create_seller_product_table_query = """
        CREATE TABLE IF NOT EXISTS m_seller_product (
            seller_product_id INT PRIMARY KEY AUTO_INCREMENT,
            sp_seller_id INT NOT NULL,
            sp_product_id INT NOT NULL,
            sp_quantity INT NOT NULL,
            sp_price DECIMAL(10, 2),
            FOREIGN KEY (sp_seller_id) REFERENCES seller(seller_id),
            FOREIGN KEY (sp_product_id) REFERENCES m_product(product_id)
        ) AUTO_INCREMENT = 3001
        """

        
        # Create Buyer Table
        create_buyer_table_query = """
        CREATE TABLE IF NOT EXISTS m_buyer (
            buyer_id INT PRIMARY KEY AUTO_INCREMENT,
            b_name VARCHAR(50) NOT NULL,
            b_sex ENUM('Male', 'Female', 'Other') NOT NULL,
            b_age INT NOT NULL,
            b_email VARCHAR(50) NOT NULL UNIQUE,
            b_password VARCHAR(50) NOT NULL,
            b_phone VARCHAR(15) NOT NULL,
            b_address TEXT NOT NULL
        ) AUTO_INCREMENT = 4001
        """

        create_m_transaction_table_query = """
        CREATE TABLE IF NOT EXISTS m_transaction (
            trans_id INT PRIMARY KEY AUTO_INCREMENT,
            mt_date DATETIME NOT NULL,
            mt_buyer_id INT NOT NULL,
            mt_total DECIMAL(10, 2) NOT NULL,
            mt_pay_method VARCHAR(15) NOT NULL,
            mt_pay_trans_no VARCHAR(50) NOT NULL,
            FOREIGN KEY (mt_buyer_id) REFERENCES m_buyer(buyer_id)
        ) AUTO_INCREMENT = 5001
        """

        create_t_transaction_table_query = """
        CREATE TABLE IF NOT EXISTS t_transaction (
            t_s_no INT PRIMARY KEY AUTO_INCREMENT,
            t_trans_id INT,
            t_seller_pro_id INT NOT NULL,
            t_seller_pro_price DECIMAL(10, 2),
            t_seller_pro_qnty DECIMAL(10, 2),
            FOREIGN KEY (t_trans_id) REFERENCES m_transaction(trans_id),
            FOREIGN KEY (t_seller_pro_id) REFERENCES m_seller_product(seller_product_id)
        )
        """

        create_m_upi_table_query = """
        CREATE TABLE IF NOT EXISTS m_upi (
            upi_code INT PRIMARY KEY AUTO_INCREMENT,
            upi_buyer_id INT NOT NULL,
            upi_id VARCHAR(15) NOT NULL,
            upi_buyer_name VARCHAR(50) NOT NULL,
            upi_balance DECIMAL(10, 2) NOT NULL
        ) AUTO_INCREMENT = 6001
        """

        create_m_card_table_query = """
        CREATE TABLE IF NOT EXISTS m_card (
            card_code INT PRIMARY KEY AUTO_INCREMENT,
            card_buyer_id INT NOT NULL,
            card_no VARCHAR(50) NOT NULL,
            card_buyer_name VARCHAR(50) NOT NULL,
            card_exp_date VARCHAR(5) NOT NULL,
            card_balance DECIMAL(10, 2) NOT NULL,
            card_cvv INT NOT NULL
        ) AUTO_INCREMENT = 7001
        """

   
        # Execute table creation queries
        cursor.execute(create_admin_table_query)
        cursor.execute(create_seller_table_query)
        cursor.execute(create_product_table_query)

        cursor.execute(create_seller_product_table_query)  
        cursor.execute(create_buyer_table_query)
        cursor.execute(create_m_transaction_table_query)  

        cursor.execute(create_t_transaction_table_query)
        cursor.execute(create_m_upi_table_query)
        cursor.execute(create_m_card_table_query)
        

        # SQL query to update or insert the admin record
        update_admin_query = """
        INSERT INTO admin (a_id, a_email, a_password)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            a_email = VALUES(a_email),
            a_password = VALUES(a_password);
        """

        admin_id = 'admin'
        admin_email = "prathvibk686@gmail.com"
        admin_password = 'admin'

        # Execute the query to insert or update the admin record
        cursor.execute(update_admin_query, (admin_id, admin_email, admin_password))

        connection.commit()
        print("Admin record updated or inserted.")

        print("Admin, User, and m_file_upload tables created or already exist.")

        return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
