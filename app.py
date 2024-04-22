from flask import jsonify
from flask import Flask
from flask import json
from flask import request
from flask_cors import CORS
from datetime import date
import mysql.connector
from datetime import datetime
import pandas as pd
from flask import send_file
from datetime import datetime
import io
import xlsxwriter



app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

db_config2 = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'db_warehouse'
}

db_config = {
    'host': 'localhost',
    'user': 'n1477318_admincapitols',
    'password': 'Ohno210500!',
    'database': 'n1477318_db_warehouse'
}


@app.route('/getproduct', methods=['GET'])
def getproduct():
    global db_config
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
            SELECT 
            product.id, 
            product.code, 
            product.article, 
            product.size, 
            product.qty, 
            alarm.qty_alarm,
            CASE
                WHEN product.qty < alarm.qty_alarm THEN 'PERLU RESTOCK'
                WHEN product.qty >= alarm.qty_alarm THEN 'AMAN'
                ELSE 'unknown'
            END AS alarm_status
        FROM 
            product
        LEFT JOIN 
            alarm ON product.id = alarm.id;
        '''

        cursor.execute(query)

        # Mengambil semua hasil query
        results = cursor.fetchall()

        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()
        now = datetime.now()
        dt = now.strftime("%H:%M:%S")

        return jsonify({'status': 'success', 'data': results,'date':dt})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/downloadproduct', methods=['GET'])
def downloadproduct():
    global db_config
    type = request.args.get('type')

    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query_full = '''
            SELECT product.id, product.code,product.id_category, product.article, product.size, product.qty, alarm.qty_alarm
FROM product
LEFT JOIN alarm ON product.id = alarm.id
        '''
        query_stock_only = '''
            SELECT id, code,id_category, article, size, qty FROM product
        '''
        query_alarm_only = '''
            SELECT product.id, product.code,product.id_category ,product.article, product.size, alarm.qty_alarm
FROM product
LEFT JOIN alarm ON product.id = alarm.id
        '''

        if type == 'full':
            cursor.execute(query_full)
            f_name = 'product_full'
        elif type == 'stock':
            cursor.execute(query_stock_only)
            f_name = 'product_stock'
        elif type == 'alarm':
            cursor.execute(query_alarm_only)
            f_name = 'product_alarm'

        # Mengambil semua hasil query sebagai DataFrame menggunakan pandas
        df = pd.DataFrame(cursor.fetchall())

        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()

        # Menghasilkan file Excel menggunakan pandas dan xlsxwriter
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Products', index=False)

        # Menambahkan informasi waktu unduh
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'{f_name}_{now}.xlsx'
        writer.close()

        # Mengatur posisi byte di awal file
        output.seek(0)

        return send_file(
            output,
            download_name=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return str(e), 500  # atau sesuaikan dengan kode status yang sesuai

@app.route('/upload', methods=['POST'])
def upload_file():
    # Memeriksa apakah terdapat file dalam request
    if 'file' not in request.files:
        return 'File not uploaded', 400

    file = request.files['file']

    # Memeriksa apakah nama file tidak kosong
    if file.filename == '':
        return 'File name not specified', 400

    # Simpan file di server
    file_path = 'uploads/' + file.filename
    file.save(file_path)

# Membaca file Excel menggunakan pandas
    try:
        df = pd.read_excel(f'{file_path}')
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM product")
    except Exception as e:
        print(e)
        return f'Error reading Excel file: {str(e)}', 500

    # Menyimpan data ke database
    try:
        for index, row in df.iterrows():
            id = int(row['id'])
            id_category = int(row['id_category'])
            code = row['code']
            article = row['article']
            size = row['size']
            qty = int(row['qty'])

            # Query untuk menyimpan data ke database
            insert_query = f"INSERT IGNORE INTO product (`id`, `id_category`,`code`, `article`, `size`, `qty`) VALUES (%s, %s, %s, %s, %s, %s)"

            cursor.execute(insert_query, (id,id_category, code, article, size, qty))
        connection.commit()
        cursor.close()
        connection.close()
        return 'Data uploaded successfully to database', 200

    except Exception as e:
        print(str(e))
        return f'Error uploading data to database: {str(e)}', 500
    
@app.route('/uploadalarm', methods=['POST'])
def upload_alarm():
    # Memeriksa apakah terdapat file dalam request
    if 'file' not in request.files:
        return 'File not uploaded', 400

    file = request.files['file']

    # Memeriksa apakah nama file tidak kosong
    if file.filename == '':
        return 'File name not specified', 400

    # Simpan file di server
    file_path = 'alarm/' + file.filename
    file.save(file_path)

# Membaca file Excel menggunakan pandas
    try:
        df = pd.read_excel(f'{file_path}')
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM alarm")
    except Exception as e:
        print(e)
        return f'Error reading Excel file: {str(e)}', 500

    # Menyimpan data ke database
    try:
        for index, row in df.iterrows():
            id = int(row['id'])
            qty_alarm = int(row['qty_alarm'])

            # Query untuk menyimpan data ke database
            insert_query = f"INSERT IGNORE INTO alarm (`id`,  `qty_alarm`) VALUES (%s, %s)"

            cursor.execute(insert_query, (id,qty_alarm))
        connection.commit()
        cursor.close()
        connection.close()
        return 'Data uploaded successfully to database', 200

    except Exception as e:
        print(str(e))
        return f'Error uploading data to database: {str(e)}', 500

@app.route('/dropproduct', methods=['GET'])
def dropproduct():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM product")
    connection.commit()
    cursor.close()
    connection.close()
    return 'Data Delete successfully', 200


if __name__ == '__main__':
    app.run(debug=True)