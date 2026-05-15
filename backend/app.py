from flask import Flask, render_template, request,redirect,session
import mysql.connector
import os

app = Flask(__name__,
            template_folder='../frontend',
            static_folder='../frontend/assets'
    )
app.secret_key = "kopiko123"

# koneksi database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123",
    database="db_kopiko"
)

cursor = db.cursor()

# halaman awal
@app.route('/')
def home():
    return render_template('login.html')

# proses login
@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    cursor.execute(
        "SELECT * FROM pengguna WHERE username=%s",
        (username,)
    )

    user = cursor.fetchone()

    if user:

        if password == user[2]:
            akses = user[3]

             # simpan session
            session['idUser'] = user[0]
            session['username'] = user[1]
            session['akses'] = user[3]

                # redirect sesuai role
            if akses == "admin":
                return redirect('/admin')

            elif akses == "owner":
                return redirect('/owner')

            elif akses == "kasir":
                return redirect('/kasir')

            else:
                return "Role tidak dikenali"

        else:
            return "Password salah"

    else:
        return "User tidak ditemukan"


# dashboard admin
@app.route('/admin')
def admin():

    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM pengguna"
    )
    totalUser = cursor.fetchone()[0]


    cursor.execute(
        "SELECT COUNT(*) FROM produk"
    )
    totalProduk = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM transaksi
        WHERE tanggal = CURDATE()
    """)
    totalTransaksi = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM pembelian
        WHERE tanggal = CURDATE()
    """)
    totalPembelian = cursor.fetchone()[0]


    cursor.execute("""
        SELECT *
        FROM produk
        WHERE stok <= 5
    """)
    stokTipis = cursor.fetchall()

    return render_template(
        'admin/admin.html',

        totalUser=totalUser,
        totalProduk=totalProduk,
        totalTransaksi=totalTransaksi,
        totalPembelian=totalPembelian,
        stokTipis=stokTipis
    )

# dashboard owner
@app.route('/owner')
def owner():
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    return render_template('owner.html')

# dashboard kasir
@app.route('/kasir')
def kasir():
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "kasir":
        return "Akses ditolak"
    
    cursor = db.cursor()

    cursor.execute("SELECT * FROM produk")
    dataProduk = cursor.fetchall()

    return render_template(
        'kasir/kasir.html',
        produk=dataProduk
    )
# logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ==============================
# SIMPAN TRANSAKSI
# ==============================

@app.route('/simpan_transaksi', methods=['POST'])
def simpan_transaksi():

    idUser = session['idUser']

    # total dari form
    total = int(request.form['total'])
    bayar = int(request.form['bayar'])

    # validasi pembayaran
    if bayar < total:
        return "Uang pembayaran kurang"

    kembalian = bayar - total

    # simpan ke tabel transaksi
    cursor.execute("""
        INSERT INTO transaksi(tanggal,total,bayar,kembalian,idUser)
        VALUES(CURDATE(), %s, %s, %s, %s)
    """, (total, bayar, kembalian, idUser))

    db.commit()

    # ambil id transaksi terakhir
    idTransaksi = cursor.lastrowid

    # ambil semua data produk dari form
    idProduk = request.form.getlist('idProduk[]')
    qty = request.form.getlist('qty[]')
    harga = request.form.getlist('harga[]')
    subtotal = request.form.getlist('subtotal[]')

    # loop simpan detail transaksi
    for i in range(len(idProduk)):

        cursor.execute("""
            INSERT INTO detailTransaksi
            (idTransaksi,idProduk,jumlah,harga,subtotal)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            idTransaksi,
            idProduk[i],
            qty[i],
            harga[i],
            subtotal[i]
        ))

        # kurangi stok
        cursor.execute("""
            UPDATE produk
            SET stok = stok - %s
            WHERE idProduk = %s
        """, (
            qty[i],
            idProduk[i]
        ))

    db.commit()

    return redirect(f'/struk/{idTransaksi}')

# cetak struk
@app.route('/struk/<id_transaksi>')
def struk(id_transaksi):

    cursor = db.cursor()

    # header transaksi
    cursor.execute("""
        SELECT *
        FROM transaksi
        WHERE idTransaksi=%s
    """, (id_transaksi,))

    transaksi = cursor.fetchone()

    # detail item
    cursor.execute("""
        SELECT p.namaProduk,
               d.jumlah,
               d.harga,
               d.subtotal
        FROM detailTransaksi d
        JOIN produk p
            ON p.idProduk = d.idProduk
        WHERE d.idTransaksi=%s
    """, (id_transaksi,))

    detail = cursor.fetchall()

    return render_template(
        'kasir/struk.html',
        transaksi=transaksi,
        detail=detail
    )

# kelola produk -- admin
@app.route('/kelola_produk')
def kelola_produk():

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM produk"
    )

    produk = cursor.fetchall()


    return render_template(
        'admin/kelola_produk.html',
        produk=produk
    )

@app.route('/tambah_produk', methods=['POST'])
def tambah_produk():

    namaProduk = request.form['namaProduk']
    hargaJual = request.form['hargaJual']
    stok = request.form['stok']

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO produk
        (namaProduk,hargaJual,stok)
        VALUES(%s,%s,%s)
    """,(
        namaProduk,
        hargaJual,
        stok
    ))

    db.commit()

    return redirect('/kelola_produk')

# @app.route('/edit_produk', methods=['POST'])
# def edit_produk():

#     idProduk = request.form['idProduk']
#     namaProduk = request.form['namaProduk']
#     hargaJual = request.form['hargaJual']
#     stok = request.form['stok']

#     cursor = db.cursor()

#     cursor.execute("""
#         UPDATE produk
#         SET namaProduk=%s,
#             hargaJual=%s,
#             stok=%s
#         WHERE idProduk=%s
#     """,(
#         namaProduk,
#         hargaJual,
#         stok,
#         idProduk
#     ))

#     db.commit()

#     return redirect('/kelola_produk')

@app.route('/edit_produk', methods=['POST'])
def edit_produk():

    idProduk = request.form['idProduk']
    namaProduk = request.form['namaProduk']

    hargaJual = request.form['hargaJual']

    stokBaru = int(
        request.form['stok']
    )


    cursor = db.cursor()


    # stok lama
    cursor.execute("""
        SELECT stok
        FROM produk
        WHERE idProduk=%s
    """,(idProduk,))

    stokLama = cursor.fetchone()[0]


    selisih = stokBaru - stokLama


    # update produk utama
    cursor.execute("""
        UPDATE produk
        SET namaProduk=%s,
            hargaJual=%s,
            stok=%s
        WHERE idProduk=%s
    """,(
        namaProduk,
        hargaJual,
        stokBaru,
        idProduk
    ))


    # jika stok bertambah
    if selisih > 0:


        # contoh resep latte
        if namaProduk == "Latte":


            # kopi
            cursor.execute("""
                UPDATE produk
                SET stok = stok - %s
                WHERE namaProduk='Biji Kopi'
            """,(selisih*10,))


            # cup
            cursor.execute("""
                UPDATE produk
                SET stok = stok - %s
                WHERE namaProduk='Cup'
            """,(selisih,))


            # sirup
            cursor.execute("""
                UPDATE produk
                SET stok = stok - %s
                WHERE namaProduk='Sirup'
            """,(selisih,))



        elif namaProduk == "Americano":


            cursor.execute("""
                UPDATE produk
                SET stok = stok - %s
                WHERE namaProduk='Biji Kopi'
            """,(selisih*10,))


            cursor.execute("""
                UPDATE produk
                SET stok = stok - %s
                WHERE namaProduk='Cup'
            """,(selisih,))


    db.commit()


    return redirect('/kelola_produk')

@app.route('/hapus_produk/<id>')
def hapus_produk(id):

    try:

        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM produk WHERE idProduk=%s",
            (id,)
        )

        db.commit()


    except Exception as e:

        return f"Produk tidak bisa dihapus: {e}"


    return redirect('/kelola_produk')

# kelola user -- admin
@app.route('/kelola_user')
def kelola_user():

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM pengguna"
    )

    users = cursor.fetchall()


    return render_template(
        'admin/kelola_user.html',
        users=users
    )

@app.route('/tambah_user', methods=['POST'])
def tambah_user():

    username = request.form['username']
    sandi = request.form['password']
    akses = request.form['akses']


    cursor = db.cursor()


    cursor.execute("""
        INSERT INTO pengguna
        (username,sandi,akses)
        VALUES(%s,%s,%s)
    """,(
        username,
        sandi,
        akses
    ))

    db.commit()


    return redirect('/kelola_user')

@app.route('/hapus_user/<id>')
def hapus_user(id):

    try:

        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM pengguna WHERE idUser=%s",
            (id,)
        )

        db.commit()

    except Exception as e:

        return f"User tidak bisa dihapus: {e}"

    return redirect('/kelola_user')

@app.route('/edit_user', methods=['POST'])
def edit_user():

    idUser = request.form['idUser']
    username = request.form['username']
    sandi = request.form['sandi']
    akses = request.form['akses']

    cursor = db.cursor()

    cursor.execute("""
        UPDATE pengguna
        SET username=%s,
            sandi=%s,
            akses=%s
        WHERE idUser=%s
    """,(
        username,
        sandi,
        akses,
        idUser
    ))

    db.commit()

    return redirect('/kelola_user')

# inventory -- admin
@app.route('/inventory')
def inventory():

    cursor = db.cursor()


    # barang
    cursor.execute("""
        SELECT *
        FROM produk
    """)

    produk = cursor.fetchall()


    # history
    cursor.execute("""
        SELECT *
        FROM pembelian
        ORDER BY idPembelian DESC
    """)

    pembelian = cursor.fetchall()


    return render_template(
        'admin/inventory.html',

        produk=produk,
        pembelian=pembelian
    )

if __name__ == '__main__':
    app.run(debug=True)