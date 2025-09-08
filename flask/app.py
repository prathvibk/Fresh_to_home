from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import mysql.connector
import yagmail
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import speech_recognition as sr
import re  # Regular expressions
from fuzzywuzzy import process  # For fuzzy string matching
import string
import random
from lib_file import lib_path
from mysql_tables import create_tables

app = Flask(__name__)
app.secret_key = 'salmonfish'

# CORS(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'prathvi@123',
    'database': 'salmon_fish'
}

mysql_tables_creation = create_tables()

if mysql_tables_creation:
    print('Successfully created all tables.')
else:
    print('Error occurred while creating tables.')


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ADMIN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


def get_db_connection():
    """Establish and return a database connection."""
    return mysql.connector.connect(**db_config)

@app.route('/admin_login', methods=['POST'])
def admin_login():
    try:
        # Parse JSON data from React frontend
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Ensure email and password are provided
        if not email or not password:
            return jsonify({"message": "Email and password are required!"}), 400

        # Connect to the database and verify credentials
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admin WHERE a_email = %s AND a_password = %s', (email, password))
        admin = cursor.fetchone()
        cursor.close()
        connection.close()

        if admin:
            # Set session variables
            session['admin_loggedin'] = True
            session['id'] = admin['a_id']
            session['email'] = admin['a_email']
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Incorrect email or password!"}), 401
    except mysql.connector.Error as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500



@app.route('/admin_index')
def admin_index():
    message = None 
    if 'admin_loggedin' in session:
        message = f"Welcome {session['id']}"
    return render_template('admin/admin_index.html', message=message)


@app.route('/sellers_list', methods=['GET'])
def sellers_list():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM seller')
    sellers = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('admin/sellers_list.html', sellers=sellers)


def send_email(to_email, name, login_email, login_password):
    try:
        yag = yagmail.SMTP("prathvibk686@gmail.com", "alvfhfuxiagjaait")
        
        subject = "Welcome to Our Platform"
        body = f"""
        Dear {name},

        Welcome to our platform! Your seller account has been successfully created.
        Here are your login credentials:

        Email: {login_email}
        Password: {login_password}

        Please log in to the seller portal to start managing your store.

        Best regards,
        Admin Team
        """
        
        yag.send(to=to_email, subject=subject, contents=body)
        print("Email sent successfully!")
    
    except Exception as e:
        print(f"Failed to send email. Error: {e}")


@app.route('/create_seller', methods=['GET', 'POST'])
def create_seller():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))
    message = None
    if request.method == 'POST':
        s_email = request.form['s_email']
        s_pwd = request.form['s_pwd']
        s_name = request.form['s_name']
        s_address = request.form['s_address']
        s_phone = request.form['s_phone']

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                'INSERT INTO seller (s_name, s_email, s_password, s_phone, s_address) VALUES (%s, %s, %s, %s, %s)',
                (s_name, s_email, s_pwd, s_phone, s_address)
            )
            connection.commit()
            message = "Seller created successfully!"

            send_email(
                to_email=s_email,
                name=s_name,
                login_email=s_email,
                login_password=s_pwd
            )

        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('admin/create_seller.html', message=message)


@app.route('/edit_seller/<int:s_code>', methods=['GET', 'POST'])
def edit_seller(s_code):
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))  # Redirect to login if admin is not logged in

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    if request.method == 'POST':
        s_name = request.form['s_name']
        s_email = request.form['s_email']
        s_address = request.form['s_address']
        s_phone = request.form['s_phone']

        try:
            # Fixing the query to update the seller table
            cursor.execute('UPDATE seller SET s_name=%s, s_email=%s, s_phone=%s, s_address=%s WHERE seller_id=%s',
                           (s_name, s_email, s_phone, s_address, s_code))
            connection.commit()
            message = "Seller updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('sellers_list'))  # Redirect to the sellers list after updating

    # Fixing the query to fetch seller data from the correct table (seller table)
    cursor.execute('SELECT seller_id, s_name, s_email, s_phone, s_address FROM seller WHERE seller_id=%s', (s_code,))
    seller = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('admin/edit_seller.html', seller=seller, message=message)


@app.route('/delete_seller/<int:s_code>', methods=['POST'])
def delete_seller(s_code): 
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('DELETE FROM seller WHERE seller_id=%s', (s_code,))
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('sellers_list'))


@app.route('/product_list', methods=['GET'])
def product_list():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM m_product')
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('admin/product_list.html', products=products)


UPLOAD_FOLDER = 'static/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    message = None
    uploaded_image_url = None
    if request.method == 'POST':
        p_name = request.form['p_name']
        p_remark = request.form['p_remark']
        file = request.files['p_image']

        if file and allowed_file(file.filename):
            # Save the image in the specified folder
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_image_url = f"{UPLOAD_FOLDER}/{filename}"

            # Save product details to the database
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    'INSERT INTO m_product (p_name, p_image, p_remark) VALUES (%s, %s, %s)',
                    (p_name, filename, p_remark)
                )
                connection.commit()
                message = "Product created successfully!"
            except Exception as err:
                message = f"Error: {err}"
            finally:
                cursor.close()
                connection.close()
        else:
            message = "Invalid file format. Please upload a valid image."

    return render_template('admin/create_product.html', message=message, uploaded_image_url=uploaded_image_url)


@app.route('/edit_product/<int:p_code>', methods=['GET', 'POST'])
def edit_product(p_code):
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    if request.method == 'POST':
        p_name = request.form['p_name']
        p_remark = request.form['p_remark']
        
        p_image = request.files.get('p_image')  # Get the uploaded image

        # Fetch the existing product details for the current product code
        cursor.execute('SELECT * FROM m_product WHERE product_id=%s', (p_code,))
        product = cursor.fetchone()

        image_path = product[2]
        
        if p_image:
            filename = secure_filename(p_image.filename)
            image_path = os.path.join('static/products', filename).replace("\\", "/")
            p_image.save(image_path)
        else:
            filename = product[2]


        try:
            cursor.execute(
                'UPDATE m_product SET p_name=%s, p_image=%s, p_remark=%s WHERE product_id=%s',
                (p_name, filename, p_remark, p_code)
            )
            connection.commit()
            message = "Product updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('product_list'))

    cursor.execute('SELECT * FROM m_product WHERE product_id=%s', (p_code,))
    product = cursor.fetchone()
    print(f"product : {product}")
    cursor.close()
    connection.close()

    return render_template('admin/edit_product.html', product=product, message=message)


@app.route('/delete_product/<int:p_code>', methods=['POST'])
def delete_product(p_code): 
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('DELETE FROM m_product WHERE product_id=%s', (p_code,))
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('product_list'))


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'admin_loggedin' not in session:
        return redirect(url_for('admin_login'))

    message = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        admin_id = session['id']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Fetch the current password from the database
            cursor.execute('SELECT a_password FROM admin WHERE a_id = %s', (admin_id,))
            admin = cursor.fetchone()

            if not admin or admin['a_password'] != current_password:
                message = "Error: Current password is incorrect."
            elif new_password != confirm_password:
                message = "Error: New password and confirmation do not match."
            else:
                # Update the password in the database
                cursor.execute('UPDATE admin SET a_password = %s WHERE a_id = %s', (new_password, admin_id))
                connection.commit()
                message = "Password updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('admin/change_password.html', message=message)


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect("http://localhost:3000")


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Seller <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


@app.route('/seller_login', methods=['GET', 'POST'])
def seller_login():
    message = None  
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM seller WHERE s_email = %s AND s_password = %s', (email, password))
        seller = cursor.fetchone()
        cursor.close()
        connection.close()

        if seller:
            session['seller_loggedin'] = True
            session['seller_id'] = seller['seller_id']
            session['seller_name'] = seller['s_name']
            session['seller_email'] = seller['s_email']
            return redirect(url_for('seller_index'))
        else:
            message = 'Incorrect email or password!'

    return render_template('seller/seller_login.html', message=message)


@app.route('/seller_index')
def seller_index():
    message = None 
    if 'seller_loggedin' in session:
        message = f"Welcome {session['seller_name']}"
    return render_template('seller/seller_index.html', message=message)


@app.route('/seller_profile', methods=['GET'])
def seller_profile():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    s_code = session['seller_id']

    # Fetch seller data from the database
    cursor.execute('SELECT * FROM seller WHERE seller_id=%s', (s_code,))
    seller = cursor.fetchone()
    
    cursor.close()
    connection.close()

    # Pass the seller variable to the template
    return render_template('seller/seller_profile.html', seller=seller, message=message)


@app.route('/admin_product_list', methods=['GET'])
def admin_product_list():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM m_product')
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('seller/admin_product_list.html', products=products)


@app.route('/seller_product_list', methods=['GET'])
def seller_product_list():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT m.seller_product_id, m.sp_product_id, p.p_name, m.sp_quantity, m.sp_price
        FROM m_seller_product m
        JOIN m_product p ON m.sp_product_id = p.product_id
        WHERE m.sp_seller_id = %s
    ''', (session['seller_id'],))
    
    products = cursor.fetchall()

    print(f"\n Products : {products} \n")

    cursor.close()
    connection.close()

    return render_template('seller/seller_product_list.html', products=products)


@app.route('/update_seller/<int:s_code>', methods=['GET', 'POST'])
def update_seller(s_code):
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    if request.method == 'POST':
        s_name = request.form['s_name']
        s_email = request.form['s_email']
        s_address = request.form['s_address']
        s_phone = request.form['s_phone']

        try:
            cursor.execute('UPDATE seller SET s_name=%s, s_email=%s, s_phone=%s, s_address=%s WHERE seller_id=%s',
                           (s_name, s_email, s_phone, s_address, s_code))
            connection.commit()
            message = "Seller updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('seller_profile'))

    cursor.execute('SELECT seller_id, s_name, s_email, s_phone, s_address FROM seller WHERE seller_id=%s', (s_code,))
    seller = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('seller/update_seller.html', seller=seller, message=message)


@app.route('/seller_add_product', methods=['GET', 'POST'])
def add_product():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    seller_id = session['seller_id']  # Get seller_id from the session
    message = None

    # Fetch available products from the product table
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute('SELECT product_id, p_name FROM m_product')
        products = cursor.fetchall()
        print(f"\n Products List : {products}")
    except mysql.connector.Error as err:
        products = []
        message = f"Error fetching products: {err}"

    if request.method == 'POST':
        sp_product_id = request.form['sp_product_id']
        sp_quantity = request.form['sp_quantity']
        sp_price = request.form['sp_price']

        try:
            # Insert the seller's product into the m_seller_product table
            cursor.execute('''
                INSERT INTO m_seller_product (sp_seller_id, sp_product_id, sp_quantity, sp_price)
                VALUES (%s, %s, %s, %s)
            ''', (seller_id, sp_product_id, sp_quantity, sp_price))
            connection.commit()

            message = "Product added successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template(
        'seller/add_product.html',
        message=message,
        products=products
    )


@app.route('/edit_seller_product/<int:product_id>', methods=['GET', 'POST'])
def edit_seller_product(product_id):
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch the product details using the product_id
    cursor.execute('''
        SELECT m.seller_product_id, m.sp_product_id, p.p_name, m.sp_quantity, m.sp_price
        FROM m_seller_product m
        JOIN m_product p ON m.sp_product_id = p.product_id
        WHERE m.seller_product_id = %s AND m.sp_seller_id = %s
    ''', (product_id, session['seller_id']))
    
    product = cursor.fetchone()
    
    if not product:
        return redirect(url_for('seller_product_list'))  # Redirect if product not found
    
    if request.method == 'POST':
        # Get the new values from the form
        sp_quantity = request.form['sp_quantity']
        sp_price = request.form['sp_price']

        # Update the product details in the m_seller_product table
        cursor.execute('''
            UPDATE m_seller_product
            SET sp_quantity = %s, sp_price = %s
            WHERE seller_product_id = %s
        ''', (sp_quantity, sp_price, product_id))
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('seller_product_list'))  # Redirect to product list after updating

    cursor.close()
    connection.close()

    return render_template('seller/edit_seller_product.html', product=product)


@app.route('/delete_seller_product/<int:sp_id>', methods=['POST'])
def delete_seller_product(sp_id): 
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('DELETE FROM m_seller_product WHERE seller_product_id=%s', (sp_id,))
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('seller_product_list'))


@app.route('/sales_report', methods=['GET'])
def sales_report():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    # Establish database connection
    connection = get_db_connection()
    cursor = connection.cursor()

    # Define the query
    query = """
    SELECT
        mt.mt_date AS transaction_date,
        s.s_name AS seller_name,
        b.b_name AS buyer_name,
        p.p_name AS product_name,
        tt.t_seller_pro_qnty AS quantity_purchased,
        sp.sp_price AS product_price
    FROM
        t_transaction tt
    JOIN
        m_transaction mt ON tt.t_trans_id = mt.trans_id
    JOIN
        m_buyer b ON mt.mt_buyer_id = b.buyer_id
    JOIN
        m_seller_product sp ON tt.t_seller_pro_id = sp.seller_product_id
    JOIN
        seller s ON sp.sp_seller_id = s.seller_id
    JOIN
        m_product p ON sp.sp_product_id = p.product_id
    ORDER BY
        s.s_name, b.b_name, p.p_name, mt.mt_date;
    """

    # Execute the query
    cursor.execute(query)
    seller_sales = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Return the results to the template
    return render_template('seller/sales_report.html', seller_sales=seller_sales)


@app.route('/seller_change_password', methods=['GET', 'POST'])
def seller_change_password():
    if 'seller_loggedin' not in session:
        return redirect(url_for('seller_login'))

    message = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        seller_id = session['seller_id']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Fetch the current password from the database
            cursor.execute('SELECT s_password FROM seller WHERE seller_id = %s', (seller_id,))
            seller = cursor.fetchone()

            if not seller or seller['s_password'] != current_password:
                message = "Error: Current password is incorrect."
            elif new_password != confirm_password:
                message = "Error: New password and confirmation do not match."
            else:
                # Update the password in the database
                cursor.execute('UPDATE seller SET s_password = %s WHERE seller_id = %s', (new_password, seller_id))
                connection.commit()
                message = "Password updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('seller/change_password.html', message=message)



@app.route('/seller_logout')
def seller_logout():
    session.clear()
    return redirect("http://localhost:3000")


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Buyer <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


@app.route('/create_buyer', methods=['GET', 'POST'])
def create_buyer():
    message = None
    if request.method == 'POST':
        b_name = request.form['b_name']
        b_sex = request.form['b_sex']
        b_age = request.form['b_age']
        b_email = request.form['b_email']
        b_password = request.form['b_password']
        b_phone = request.form['b_phone']
        b_address = request.form['b_address']

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                'INSERT INTO m_buyer (b_name, b_sex, b_age, b_email, b_password, b_phone, b_address) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (b_name, b_sex, b_age, b_email, b_password, b_phone, b_address)
            )
            connection.commit()
            # message = "Your account created successfully!"

            # Set the message in session
            session['message'] = "Your account was created successfully!"

            # Send email notification
            send_email(
                to_email=b_email,
                name=b_name,
                login_email=b_email,
                login_password=b_password
            )

            return redirect(url_for('buyer_login'))

        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('buyer/create_buyer.html', message=message)


@app.route('/buyer_login', methods=['GET', 'POST'])
def buyer_login():
    message = None  
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM m_buyer WHERE b_email = %s AND b_password = %s', (email, password))
        buyer = cursor.fetchone()
        cursor.close()
        connection.close()

        if buyer:
            session['buyer_loggedin'] = True
            session['buyer_id'] = buyer['buyer_id']
            session['buyer_name'] = buyer['b_name']
            session['buyer_phone'] = buyer['b_phone']
            session['buyer_email'] = buyer['b_email']

            return redirect(url_for('buyer_index'))
        else:
            message = 'Incorrect email or password!'

    return render_template('buyer/buyer_login.html', message=message)


@app.route('/buyer_index')
def buyer_index():
    message = None 
    if 'buyer_loggedin' in session:
        message = f"Welcome {session['buyer_name']}"
    return render_template('buyer/buyer_index.html', message=message)


@app.route('/products_index', methods=['GET'])
def products_index():
    welcome_message = None
    products = []
    unique_p_names = []
    
    buyer_name = session['buyer_name']

    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))

    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch unique product names from the database
    try:
        cursor.execute("SELECT DISTINCT mp.p_name FROM m_seller_product sp INNER JOIN m_product mp ON sp.sp_product_id = mp.product_id")
        unique_p_names = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print("Error filtering products:", e)

    # Fetch filtered or all product details from the database
    try:
        name_filter = request.args.get('name')  # Get the 'name' query parameter from the URL

        # If a filter is provided, use it in the query; otherwise, fetch all products
        if name_filter:
            query = """
            SELECT 
                sp.seller_product_id,
                sp.sp_seller_id,
                seller.s_name,
                sp.sp_product_id, 
                mp.p_name, 
                mp.p_image, 
                mp.p_remark, 
                sp.sp_quantity, 
                sp.sp_price 
            FROM 
                m_seller_product sp
            INNER JOIN 
                m_product mp 
            ON 
                sp.sp_product_id = mp.product_id
            INNER JOIN 
                seller
            ON 
                sp.sp_seller_id = seller.seller_id
            WHERE 
                mp.p_name = %s
            """
            cursor.execute(query, (name_filter,))
        else:
            query = """
            SELECT 
                sp.seller_product_id,
                sp.sp_seller_id,
                seller.s_name,
                sp.sp_product_id, 
                mp.p_name, 
                mp.p_image, 
                mp.p_remark, 
                sp.sp_quantity, 
                sp.sp_price 
            FROM 
                m_seller_product sp
            INNER JOIN 
                m_product mp 
            ON 
                sp.sp_product_id = mp.product_id
            INNER JOIN 
                seller
            ON 
                sp.sp_seller_id = seller.seller_id
            """
            cursor.execute(query)
        
        products = cursor.fetchall()
    except Exception as e:
        print("Error fetching products:", e)
    finally:
        cursor.close()
        connection.close()

        welcome_message = f"Welcome {session['buyer_name']}"

    return render_template('buyer/products.html', wel_msg=welcome_message, products=products, unique_p_names=unique_p_names)


# @app.route('/selected_products', methods=['POST'])
# def selected_products():
#     data = request.get_json()
#     selected_items = data.get('items', [])
    
#     # Calculate Total Price for each product and Total Amount
#     for item in selected_items:
#         item['totalPrice'] = item['quantity'] * item['productPrice']
    
#     # Calculate Total Amount
#     total_amount = sum(item['totalPrice'] for item in selected_items)
    
#     # print("Selected items received:", selected_items)
#     # print("Total Amount:", total_amount)

#     # Save selected items to session
#     session['selected_items'] = selected_items

#     # Render the HTML page
#     return render_template('buyer/selected_products.html', selected_items=selected_items, total_amount=total_amount)



@app.route('/selected_products', methods=['POST', 'GET'])
def selected_products():
    if request.method == 'POST':
        # Parse data from the POST request
        data = request.get_json()
        selected_items = data.get('items', [])
        
        # Calculate Total Price for each product
        for item in selected_items:
            item['totalPrice'] = item['quantity'] * item['productPrice']
        
        # Calculate Total Amount
        total_amount = sum(item['totalPrice'] for item in selected_items)

        # Save selected items and total amount to session
        session['selected_items'] = selected_items
        session['total_amount'] = total_amount
    else:
        # Handle GET request (for redirection or error cases)
        selected_items = session.get('selected_items', [])
        total_amount = session.get('total_amount', 0)
    
    # Optional: Get error message from query parameters
    message = request.args.get('message', '')

    # Render the HTML page
    return render_template('buyer/selected_products.html', selected_items=selected_items, total_amount=total_amount, message=message)


# Payment processing route
@app.route('/payment_process', methods=['GET', 'POST'])
def payment_process():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))
    
    buyer_id = session['buyer_id']

    selected_items = session.get('selected_items', [])
    # print(f"\n selected_items : {selected_items}")

    # Calculate total amount from session
    total_amount = sum(item['totalPrice'] for item in selected_items)

    print(f"total_amount : {total_amount}")

    payment_method = request.form['payment_method']

    payment_info = json.loads(request.form['payment_info'])  # payment_info contains JSON for card/UPI details

    # print(f"\n payment_method, payment_info : {payment_method, payment_info}")

    if payment_method not in ['card', 'upi']:
        print(f"\n Invalid payment method. Please try again.")
        return redirect(url_for('products_index', message="Invalid payment method. Please try again."))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT b_password FROM m_buyer WHERE buyer_id = %s", (buyer_id,))
    buyer_password = cursor.fetchone()

    print(f"\n buyer_password : {buyer_password}")

    if not buyer_password:
        print("Buyer not found.")
        return redirect(url_for('payment_process', message="Buyer not found."))

    buyer_password = buyer_password[0] 

    print(f"\n buyer_password : {buyer_password}")
    
    if payment_method == 'card':
        
        # Extract card details
        card_no = payment_info.get('card_no')
        card_name = payment_info.get('card_name')
        card_exp_date = payment_info.get('card_exp_date')
        card_cvv = payment_info.get('card_cvv')
        card_password = payment_info.get('password')

        print(f"\n Card details : {card_no, card_name, card_exp_date, card_cvv, card_password}")

        if card_password != buyer_password:
            session['payment_details'] = payment_info  # Save payment details in session
            message = "Incorrect {} password. Please try again.".format(payment_method.capitalize())
            print("Card password is incorrect.")
            return redirect(url_for('selected_products', message=message))

        # Verify card details in the database
        cursor.execute(""" 
            SELECT card_code, card_balance FROM m_card 
            WHERE card_buyer_id = %s AND card_no = %s AND card_buyer_name = %s 
            AND card_exp_date = %s AND card_cvv = %s
        """, (buyer_id, card_no, card_name, card_exp_date, card_cvv))
        card_result = cursor.fetchone()

        session['payment_result'] = card_result

        print(f"\n card_result : {card_result}")

        if not card_result:
            return redirect(url_for('selected_products', message="Invalid card details. Please try again."))
        elif card_result[1] < total_amount:
            return redirect(url_for('selected_products', message="You don't have sufficient balance to purchase."))

        # Update card balance after successful payment
        new_balance = card_result[1] - total_amount
        print(f"\n new_balance: {new_balance}")

        cursor.execute("""
            UPDATE m_card
            SET card_balance = %s
            WHERE card_buyer_id = %s AND card_no = %s
        """, (new_balance, buyer_id, card_no))
        connection.commit()  # Commit the transaction to save changes

    elif payment_method == 'upi':
        # Extract UPI details
        upi_id = payment_info.get('upi_id')
        upi_password = payment_info.get('password')

        # print(f"\n upi details : {upi_id, upi_password}")

        if upi_password != buyer_password:
            print("UPI password is incorrect.")
            return redirect(url_for('selected_products', message="Incorrect UPI password. Please try again."))

        # Verify UPI details in the database
        cursor.execute(""" 
            SELECT upi_code, upi_balance FROM m_upi 
            WHERE upi_buyer_id = %s AND upi_id = %s
        """, (buyer_id, upi_id))
        upi_result = cursor.fetchone()

        session['payment_result'] = upi_result

        print(f"\n upi_result : {upi_result}")

        if not upi_result:
            return redirect(url_for('selected_products', message="Invalid UPI details. Please try again."))
        elif upi_result[1] < total_amount:
            return redirect(url_for('selected_products', message="You don't have sufficient balance to purchase."))

        # Update card balance after successful payment
        new_balance = upi_result[1] - total_amount
        print(f"\n new_balance: {new_balance}")

        cursor.execute("""
            UPDATE m_upi
            SET upi_balance = %s
            WHERE upi_buyer_id = %s AND upi_id = %s
        """, (new_balance, buyer_id, upi_id))
        connection.commit()

    # Store payment details in session
    session['payment_method'] = payment_method
    session['payment_trans_no'] = payment_info

    return redirect(url_for('purchase_products'))


def send_email_purchase(recipient, subject, body):
    try:
        yag = yagmail.SMTP('prathvibk686@gmail.com', 'alvfhfuxiagjaait')
        yag.send(to=recipient, subject=subject, contents=body)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Purchase products route
@app.route('/purchase_products', methods=['GET', 'POST'])
def purchase_products():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))
    
    buyer_id = session['buyer_id']
    buyer_email = session['buyer_email']

    selected_items = session.get('selected_items', [])
    payment_method = session.get('payment_method')
    payment_trans_no = session.get('payment_trans_no')

    upi_id = payment_trans_no.get('upi_id')


    # print(f"payment_method : {payment_method}")
    # print(f"payment_trans_no : {payment_trans_no}")

    # Validate session data
    if not selected_items:
        return redirect(url_for('selected_products', message="No items selected for purchase."))
    if not payment_method or not payment_trans_no:
        return redirect(url_for('selected_products', message="Payment details are missing. Please try again."))

    total_amount = sum(item['totalPrice'] for item in selected_items)

    # print(f"\n purchase_products selected_items, payment_method, payment_trans_no, total_amount : {selected_items, payment_method, payment_trans_no, total_amount}")

    payment_result = session.get('payment_result')

    # Database connection and stock update logic
    try:
        if payment_method == 'card':
            payment_trans_code = payment_result[0]  # card_code
        elif payment_method == 'upi':
            payment_trans_code = payment_result[0]  # upi_code

        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert into m_transaction table
        insert_m_transaction_query = """
        INSERT INTO m_transaction (mt_date, mt_buyer_id, mt_total, mt_pay_method, mt_pay_trans_no)
        VALUES (%s, %s, %s, %s, %s)
        """
        transaction_date = datetime.now()
        cursor.execute(insert_m_transaction_query, (transaction_date, buyer_id, total_amount, payment_method, payment_trans_code))
        
        # Get the generated transaction ID
        transaction_id = cursor.lastrowid

        print(f"\n purchase_products transaction_id : {transaction_id}")
        
        for item in selected_items:
            product_id = item['productId']
            quantity_purchased = item['quantity']
            product_price = item['productPrice']
            

            # Insert into t_transaction table
            insert_t_transaction_query = """
            INSERT INTO t_transaction (t_trans_id, t_seller_pro_id, t_seller_pro_price, t_seller_pro_qnty)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_t_transaction_query, (transaction_id, product_id, product_price, quantity_purchased))
            
            # Update stock query
            update_stock_query = """
            UPDATE m_seller_product
            SET sp_quantity = sp_quantity - %s
            WHERE seller_product_id = %s
            """
            cursor.execute(update_stock_query, (quantity_purchased, product_id))
        
        connection.commit()

        session.pop('selected_items', None)
        session.pop('payment_method', None)
        session.pop('payment_trans_no', None)

        # Prepare email content
        email_subject = "Purchase Confirmation - Fish Mart"
        email_body = f"""
        Dear Buyer,

        Thank you for your purchase. Here are your order details:

        Products:
        """
        for item in selected_items:
            email_body += f"- {item['productName']}: {item['quantity']} x ₹{item['productPrice']} = ₹{item['totalPrice']}\n"

        email_body += f"\nTotal Amount: ₹{total_amount}\n\nThank you for shopping with us!\n\nRegards,\nFish Mart"

        # Send email
        email_status = send_email_purchase(buyer_email, email_subject, email_body)

        print(f"\n email_status : {email_status}")
        
        if email_status:
            print("Purchase successful and successfully shared confirmation email.")
        else:
            print("Purchase successful, but there was an issue sending the confirmation email.")


        return redirect(url_for('products_index', message="Purchase successful! Your stock has been updated."))
    except Exception as e:
        print("Error updating stock:", e)
        connection.rollback()
        return redirect(url_for('products_index', message="There was an issue processing your purchase. Please try again."))
    finally:
        cursor.close()
        connection.close()


# List of available fish names
# available_fish = ["Salmon", "Tuna", "Mackerel", "Sardines", "Trout", "Herring"]


# Function to fetch available fish names dynamically
def get_available_fish():
    try:
        # Connect to the database using db_config from app.py
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Query to fetch fish names from the table
        cursor.execute("SELECT p_name FROM m_product")
        fish_list = [row[0] for row in cursor.fetchall()]  # Fetch all fish names

        # Close connection
        cursor.close()
        conn.close()

        return fish_list

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []  # Return empty list in case of an error
    

# Function to handle speech recognition
def speech_to_text():
    available_fish = get_available_fish()  # Get dynamic list of fish names

    print("available_fish : ", available_fish)

    if not available_fish:
        return {"status": "error", "message": "No fish names available in the database."}
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        print("audio : ", audio)

    try:
        text = recognizer.recognize_google(audio)
        print("---------------------------------------------------------------------")
        print(f"You said: {text}")
        print("---------------------------------------------------------------------")

        # Extract quantity, unit, and fish name
        match = re.search(r"(\d+)\s*(kg|kilo|kilograms)?\s*(.*)", text, re.IGNORECASE)
        if match:
            quantity = match.group(1)  # Extract quantity
            unit = match.group(2)  # Extract unit (optional)
            fish_name = match.group(3).strip()  # Extract the rest (fish name)

            # Clean the fish name by removing "fish" and extra spaces
            fish_name = re.sub(r'\bfish\b', '', fish_name, flags=re.IGNORECASE).strip()

            # Use fuzzy matching to find the closest fish name
            best_match, confidence = process.extractOne(fish_name, available_fish)
            print("best_match, confidence : ", best_match, confidence)

            if confidence >= 40:  # Accept matches with confidence >= 40%
                return {
                    "status": "success",
                    "message": f"You said: {text}",
                    "quantity": quantity,
                    "unit": unit if unit else "kg",  # Default to 'kg' if no unit is provided
                    "fish_name": best_match,  # The closest matched fish name
                    "confidence": f"{confidence}% match"
                }
            else:
                return {"status": "error", "message": f"Product '{fish_name}' not found! Closest match: '{best_match}' with {confidence}% confidence."}

        else:
            return {"status": "error", "message": "Could not extract fish name and quantity."}

    except sr.UnknownValueError:
        return {"status": "error", "message": "Sorry, I could not understand the audio."}
    except sr.RequestError:
        return {"status": "error", "message": "Could not request results from the speech service."}


@app.route("/listen", methods=["POST"])
def listen():
    # Call the speech recognition function
    result = speech_to_text()
    return jsonify(result)


@app.route('/buyer_profile', methods=['GET'])
def buyer_profile():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    b_code = session['buyer_id']

    cursor.execute('SELECT * FROM m_buyer WHERE buyer_id=%s', (b_code,))
    buyer = cursor.fetchone()

    print(f"\n buyer : {buyer}")
    
    cursor.close()
    connection.close()

    return render_template('buyer/buyer_profile.html', buyer=buyer, message=message)


@app.route('/update_buyer/<int:b_code>', methods=['GET', 'POST'])
def update_buyer(b_code):
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    message = None

    if request.method == 'POST':
        b_name = request.form['b_name']
        b_sex = request.form['b_sex']
        b_age = request.form['b_age']
        b_email = request.form['b_email']
        b_phone = request.form['b_phone']
        b_address = request.form['b_address']

        if not b_name or not b_email or not b_phone:
            message = "Error: Name, email, and phone are required!"
        else:
            try:
                cursor.execute('UPDATE m_buyer SET b_name=%s, b_sex=%s, b_age=%s, b_email=%s, b_phone=%s, b_address=%s WHERE buyer_id=%s',
                               (b_name, b_sex, b_age, b_email, b_phone, b_address, b_code))
                connection.commit()
                message = "Buyer updated successfully!"
            except mysql.connector.Error as err:
                message = f"Error: {err}"
            finally:
                cursor.close()
                connection.close()
            return redirect(url_for('buyer_profile'))

    cursor.execute('SELECT buyer_id, b_name, b_sex, b_age, b_email, b_phone, b_address FROM m_buyer WHERE buyer_id=%s', (b_code,))
    buyer = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('buyer/update_buyer.html', buyer=buyer, message=message)


@app.route('/buyer_change_password', methods=['GET', 'POST'])
def buyer_change_password():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))

    message = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        buyer_id = session['buyer_id']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Fetch the current password from the database
            cursor.execute('SELECT b_password FROM m_buyer WHERE buyer_id = %s', (buyer_id,))
            buyer = cursor.fetchone()

            # Validate current password and new password confirmation
            if not buyer or buyer['b_password'] != current_password:
                message = "Error: Current password is incorrect."
            elif new_password != confirm_password:
                message = "Error: New password and confirmation do not match."
            elif len(new_password) < 6:  # Ensure password strength (optional)
                message = "Error: Password must be at least 6 characters long."
            else:
                # Update the password in the database
                cursor.execute('UPDATE m_buyer SET b_password = %s WHERE buyer_id = %s', (new_password, buyer_id))
                connection.commit()
                message = "Password updated successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('buyer/change_password.html', message=message)


@app.route('/privious_orders', methods=['GET'])
def privious_orders():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT t.t_s_no, t.t_trans_id, p.p_name AS product_name, t.t_seller_pro_price, 
               t.t_seller_pro_qnty, t.t_seller_pro_price * t.t_seller_pro_qnty AS total_price, 
               mt.mt_date
        FROM t_transaction t
        JOIN m_transaction mt ON t.t_trans_id = mt.trans_id
        JOIN m_seller_product sp ON t.t_seller_pro_id = sp.seller_product_id
        JOIN m_product p ON sp.sp_product_id = p.product_id  -- Join with m_product to get product name
        WHERE mt.mt_buyer_id = %s
    """, (session['buyer_id'],))  # Use buyer_id stored in session for the query
    
    orders = cursor.fetchall()

    print(f"\n orders : {orders} \n")

    cursor.close()
    connection.close()

    return render_template('buyer/previous_orders.html', orders=orders)


@app.route('/create_upi', methods=['GET', 'POST'])
def create_upi():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))
    
    buyer_id = session['buyer_id']
    buyer_name = session['buyer_name']
    buyer_phone = session['buyer_phone']

    message = None

    if request.method == 'POST':
        # Get form data from the user
        upi_id = request.form['upi_id']
        upi_buyer_name = request.form['upi_buyer_name']
        upi_balance = float(request.form['upi_balance'])

        # Insert into m_upi table
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO m_upi (upi_buyer_id, upi_id, upi_buyer_name, upi_balance)
                VALUES (%s, %s, %s, %s)
            """, (buyer_id, upi_id, upi_buyer_name, upi_balance))
            
            connection.commit()
            message = "Your UPI details have been updated successfully!"

        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            connection.close()

        return render_template('buyer/create_upi.html', message=message)

    # Generate default UPI ID and balance
    phone_last_5_digits = buyer_phone[-5:]
    random_extension = ''.join(random.choices(string.ascii_lowercase, k=3))
    upi_id = f"{phone_last_5_digits}@{random_extension}"
    upi_balance = 5000

    return render_template('buyer/create_upi.html', message=message, upi_id=upi_id, upi_buyer_name=buyer_name, upi_balance=upi_balance)



@app.route('/create_card', methods=['GET', 'POST'])
def create_card():
    if 'buyer_loggedin' not in session:
        return redirect(url_for('buyer_login'))
    
    buyer_id = session['buyer_id']
    buyer_name = session['buyer_name']
    card_balance = 5000  # Default balance

    message = None

    if request.method == 'POST':
        # Get form data from the user
        card_no = request.form['card_no']
        name_on_card = request.form['name_on_card']
        card_exp_date = request.form['card_exp_date']
        card_balance = float(request.form['card_balance'])
        card_cvv = request.form['card_cvv']

        print(f"\n card_no, name_on_card, card_exp_date, card_balance, card_cvv : {card_no, name_on_card, card_exp_date, card_balance, card_cvv}")

        # Insert into m_card table
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO m_card (card_buyer_id, card_no, card_buyer_name, card_exp_date, card_balance, card_cvv)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (buyer_id, card_no, name_on_card, card_exp_date, card_balance, card_cvv))
            
            connection.commit()
            message = "Your card details have been created successfully!"

        except mysql.connector.Error as err:
            message = f"Error: {err}"

            print(f"message : {message}")
        finally:
            cursor.close()
            connection.close()

        return render_template('buyer/create_card.html', message=message)
    
    return render_template('buyer/create_card.html', message=message, name_on_card=buyer_name, card_balance=card_balance)














@app.route('/buyer_logout')
def buyer_logout():
    session.clear()
    return render_template('buyer/buyer_login.html')


if __name__ == '__main__':
    app.run(debug=True)