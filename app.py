from flask import jsonify
from flask import Flask
from flask import request
from flask_cors import CORS
from datetime import datetime
import json
import mysql.connector
from datetime import datetime
import pandas as pd
from flask import send_file
from datetime import datetime
import io
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'



app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

db_config_2 = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'db_warehouse'
}

db_config2 = {
    'host': '109.106.252.55',
    'user': 'n1477318_admincapitols',
    'password': 'Ohno210500!',
    'database': 'n1477318_db_warehouse'
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
    
@app.route('/getproductwp', methods=['GET'])
def getproductwp():
    global db_config
    warehouse = request.args.get('warehouse')
    
    if warehouse != "99":
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
                    alarm ON product.id = alarm.id
                WHERE product.id_category = %s AND
                product.qty > 0
            '''

            # Execute the query with the parameter
            cursor.execute(query, (warehouse,))

            # Mengambil semua hasil query
            results = cursor.fetchall()

            # Menutup kursor dan koneksi
            cursor.close()
            connection.close()

            return jsonify(results)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        try:
            with open('data_dummy_cinere.json', 'r') as file:
                results = json.load(file)
        except Exception as e:
            return jsonify({'message': str(e), 'status': 'failed'})
        return jsonify(results['cinere'])

@app.route('/getselling', methods=['GET'])
def getselling():
    global db_config
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
        SELECT 
            penjualan.id,
            penjualan.admin,
            penjualan.asal,
            penjualan.bukti_tf,
            penjualan.code,
            penjualan.ekspedisi,
            penjualan.file,
            penjualan.harga,
            penjualan.jenis_pengiriman,
            penjualan.jenis_produk,
            penjualan.kode_invoice,
            penjualan.media,
            penjualan.note,
            penjualan.ongkir,
            penjualan.penerima,
            penjualan.qty,
            penjualan.rekening,
            penjualan.status_bayar,
            penjualan.tanggal,
            penjualan.toko,
            product.article,
            product.size

        FROM 
            penjualan
        LEFT JOIN 
            product ON penjualan.code = product.code;
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

        if type == 'full':
            query = '''
                SELECT product.id, product.code, product.id_category, product.article, product.size, product.qty, alarm.qty_alarm
                FROM product
                LEFT JOIN alarm ON product.id = alarm.id
            '''
            f_name = 'product_full'
        elif type == 'stock':
            query = '''
                SELECT id, code, id_category, article, size, qty
                FROM product
            '''
            f_name = 'product_stock'
        elif type == 'alarm':
            query = '''
                SELECT product.id, product.code, product.id_category, product.article, product.size, alarm.qty_alarm
                FROM product
                LEFT JOIN alarm ON product.id = alarm.id
            '''
            f_name = 'product_alarm'
        else:
            return "Invalid type specified", 400

        cursor.execute(query)

        # Membuat DataFrame langsung dari hasil query
        df = pd.DataFrame(cursor.fetchall())

        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()

        # Menentukan nama file
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'download/{f_name}_{now}.xlsx'

        # Menyimpan DataFrame ke file Excel dan mengirimkan sebagai response
        df.to_excel(filename, index=False)

        return send_file(
            filename,
            download_name=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return str(e), 500

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
        df['qty'] = (df['qty'].fillna(0)).astype(int)
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
        df =df.dropna(subset=['qty_alarm'])
        df['qty_alarm'] = df['qty_alarm'].astype(int)
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

@app.route('/getarticlemonth', methods=['GET'])
def getarticlemonth():
    global db_config
    days_count = int(request.args.get('days'))
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
        SELECT 
            penjualan.qty,
            penjualan.tanggal,
            product.article

        FROM 
            penjualan
        LEFT JOIN 
            product ON penjualan.code = product.code;
        '''

        cursor.execute(query)

        # Mengambil semua hasil query
        df = pd.DataFrame(cursor.fetchall())

        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()
        df['tanggal'] = pd.to_datetime(df['tanggal'])

        # Hitung tanggal hari ini dan 30 hari sebelumnya
        today = pd.Timestamp.now().normalize()  # Mendapatkan tanggal hari ini
        thirty_days_ago = today - pd.Timedelta(days=days_count)  # Mendapatkan tanggal 30 hari sebelumnya

        # Filter DataFrame berdasarkan rentang tanggal
        filtered_df = df[(df['tanggal'] >= thirty_days_ago) & (df['tanggal'] <= today)]

        filtered_df = df[(df['tanggal'] >= thirty_days_ago) & (df['tanggal'] <= today)]
        filtered_df
        sum_qty_per_barang = filtered_df.groupby('article')['qty'].sum().reset_index()
        sum_qty_per_barang = sum_qty_per_barang.to_dict(orient='records')


        now = datetime.now()
        dt = now.strftime("%H:%M:%S")

        return jsonify({'status': 'success', 'data': sum_qty_per_barang,'date':dt})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/getalarm', methods=['GET'])
def getalarm():
    global db_config
    count_qty = int(request.args.get('count'))
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
            SELECT 
            product.id, 
            product.article, 
            product.qty, 
            alarm.qty_alarm
        FROM 
            product
        LEFT JOIN 
            alarm ON product.id = alarm.id;
        '''

        cursor.execute(query)

        # Mengambil semua hasil query
        df = pd.DataFrame(cursor.fetchall())
        df['qty_alarm'] = (df['qty_alarm'].fillna(0)).astype(int)
        df['qty'] = (df['qty'].fillna(0)).astype(int)
        df1 = df.groupby('article')['qty'].sum().reset_index()
        df2 = df.groupby('article')['qty_alarm'].sum().reset_index()
        result = pd.merge(df1,df2,on='article',how='left')
        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()
        result['selisih'] = result['qty'] / result['qty_alarm']
        result = result.sort_values(by='selisih', ascending=True).reset_index()
        result['id'] = result.index + 1
        result = result[['id','article','qty','qty_alarm','selisih']]
        result = result.head(int(count_qty))
        result= result.to_dict(orient='records')


        now = datetime.now()
        dt = now.strftime("%H:%M:%S")

        return jsonify({'status': 'success', 'data': result,'date':dt})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/downloadalarm', methods=['GET'])
def downloadalarm():
    global db_config
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
            SELECT 
            product.id, 
            product.article, 
            product.qty, 
            alarm.qty_alarm
        FROM 
            product
        LEFT JOIN 
            alarm ON product.id = alarm.id;
        '''

        cursor.execute(query)

        # Mengambil semua hasil query
        df = pd.DataFrame(cursor.fetchall())
        df['qty_alarm'] = (df['qty_alarm'].fillna(0)).astype(int)
        df['qty'] = (df['qty'].fillna(0)).astype(int)
        df1 = df.groupby('article')['qty'].sum().reset_index()
        df2 = df.groupby('article')['qty_alarm'].sum().reset_index()
        result = pd.merge(df1,df2,on='article',how='left')
        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()
        result['selisih'] = result['qty'] / result['qty_alarm']
        result.loc[result['qty'] <= result['qty_alarm'], 'alarm_status'] = 'Perlu Restock'
        result.loc[result['qty'] > result['qty_alarm'], 'alarm_status'] = 'Aman'
        result = result.sort_values(by='selisih', ascending=True).reset_index()
        result['id'] = result.index + 1
        result = result[['id','article','qty','qty_alarm','selisih','alarm_status']]
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'download/alarmfull_{now}.xlsx'

        # Menyimpan DataFrame ke file Excel dan mengirimkan sebagai response
        result.to_excel(filename, index=False)

        return send_file(
            filename,
            download_name=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return str(e), 500
    
@app.route('/downloadbestproduct', methods=['GET'])
def downloadbestproduct():
    global db_config
    days_count = int(request.args.get('days'))
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''
        SELECT 
            penjualan.qty,
            penjualan.tanggal,
            product.article

        FROM 
            penjualan
        LEFT JOIN 
            product ON penjualan.code = product.code;
        '''

        cursor.execute(query)

        # Mengambil semua hasil query
        df = pd.DataFrame(cursor.fetchall())

        # Menutup kursor dan koneksi
        cursor.close()
        connection.close()
        df['tanggal'] = pd.to_datetime(df['tanggal'])

        # Hitung tanggal hari ini dan 30 hari sebelumnya
        today = pd.Timestamp.now().normalize()  # Mendapatkan tanggal hari ini
        thirty_days_ago = today - pd.Timedelta(days=days_count)  # Mendapatkan tanggal 30 hari sebelumnya

        # Filter DataFrame berdasarkan rentang tanggal
        filtered_df = df[(df['tanggal'] >= thirty_days_ago) & (df['tanggal'] <= today)]

        filtered_df = df[(df['tanggal'] >= thirty_days_ago) & (df['tanggal'] <= today)]
        filtered_df
        sum_qty_per_barang = filtered_df.groupby('article')['qty'].sum().reset_index()
        sum_qty_per_barang = sum_qty_per_barang.sort_values(by='qty', ascending=False)
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'download/Best_Produk_{now}.xlsx'

        # Menyimpan DataFrame ke file Excel dan mengirimkan sebagai response
        sum_qty_per_barang.to_excel(filename, index=False)

        return send_file(
            filename,
            download_name=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return str(e), 500

@app.route('/getcapacity', methods=['GET'])
def getcapacity():
    global db_config
    try:
        # Membuat koneksi ke database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = '''SELECT product.id_category, CAST(SUM(product.qty) AS INT) AS total_qty, category.capacity, category.category FROM product LEFT JOIN category ON product.id_category = category.id GROUP BY product.id_category, category.capacity, category.category;'''

        cursor.execute(query)
        response = cursor.fetchall()

        cursor.close()
        connection.close()

        now = datetime.now()
        dt = now.strftime("%H:%M:%S")

        return jsonify({'status': 'success', 'data': response,'date':dt})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/sysstatus', methods=['GET'])
def sysstatus():
    #CARI SISTEM STATUS
    global db_config
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = '''SELECT OPTIONS, VALUE FROM `system` WHERE options = "system_status" '''
        cursor.execute(query)
        # Mengambil semua hasil query
        system_status = cursor.fetchall()
        cursor.close()
        conn.close()
        system_status = system_status[0]['VALUE']
    except Exception as e:
        return jsonify({'message': str(e), 'status':'failed'})
    
    return jsonify({'message': 'Data received successfully', 'status':'success','SystemStatus':system_status})

@app.route('/toggle_sysstatus', methods=['POST'])
def toggle_sysstatus():
    global db_config
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Mendapatkan status sistem saat ini
        query = '''SELECT OPTIONS, VALUE FROM `system` WHERE options = "system_status" '''
        cursor.execute(query)
        system_status = cursor.fetchall()
        current_status = int(system_status[0]['VALUE'])
        
        # Mengubah status
        new_status = 1 if current_status == 0 else 0
        
        # Memperbarui status di database
        update_query = '''UPDATE `system` SET VALUE = %s WHERE options = "system_status" '''
        cursor.execute(update_query, (new_status,))
        conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'failed'})
    
    return jsonify({'message': 'System status updated successfully', 'status': 'success', 'NewSystemStatus': new_status})

if __name__ == '__main__':
    app.run(debug=False)