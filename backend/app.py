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
    database="db_kopiko2"
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

    # total user
    cursor.execute(
        "SELECT COUNT(*) FROM pengguna"
    )
    totalUser = cursor.fetchone()[0]

    # total produk/menu
    cursor.execute(
        "SELECT COUNT(*) FROM produk"
    )
    totalProduk = cursor.fetchone()[0]

    # total transaksi hari ini
    cursor.execute("""
        SELECT COUNT(*)
        FROM transaksi
        WHERE DATE(tanggal)=CURDATE()
    """)
    totalTransaksi = cursor.fetchone()[0]

    # total pembelian hari ini
    cursor.execute("""
        SELECT COUNT(*)
        FROM pembelian
        WHERE DATE(tanggal)=CURDATE()
    """)
    totalPembelian = cursor.fetchone()[0]

    # stok bahan baku menipis
    cursor.execute("""
        SELECT *
        FROM bahanBaku
        WHERE stok <= 100
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

# KELOLA PRODUK
# halaman produk - admin
@app.route('/kelola_produk')
def kelola_produk():

    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM produk
        ORDER BY idProduk asc
    """)

    produk = cursor.fetchall()

    return render_template(
        'admin/kelola_produk.html',
        produk=produk
    )

@app.route('/tambah_produk', methods=['POST'])
def tambah_produk():

    namaProduk = request.form['namaProduk']
    kategori = request.form['kategori']
    hargaJual = request.form['hargaJual']
    satuan = request.form['satuan']
    tipeProduk = request.form['tipeProduk']

    cursor = db.cursor()

    query = """
        INSERT INTO produk
        (
            namaProduk,
            kategori,
            hargaJual,
            satuan,
            tipeProduk
        )
        VALUES (%s,%s,%s,%s,%s)
    """

    value = (
        namaProduk,
        kategori,
        hargaJual,
        satuan,
        tipeProduk
    )

    cursor.execute(query, value)

    db.commit()

    return redirect('/kelola_produk')

@app.route('/edit_produk', methods=['POST'])
def edit_produk():

    idProduk = request.form['idProduk']
    namaProduk = request.form['namaProduk']
    kategori = request.form['kategori']
    hargaJual = request.form['hargaJual']
    satuan = request.form['satuan']
    tipeProduk = request.form['tipeProduk']

    cursor = db.cursor()

    cursor.execute("""
        UPDATE produk
        SET
            namaProduk=%s,
            kategori=%s,
            hargaJual=%s,
            satuan=%s,
            tipeProduk=%s
        WHERE idProduk=%s
    """, (
        namaProduk,
        kategori,
        hargaJual,
        satuan,
        tipeProduk,
        idProduk
    ))

    db.commit()

    return redirect('/kelola_produk')

@app.route('/hapus_produk/<id>')
def hapus_produk(id):

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM produk
        WHERE idProduk=%s
    """, (id,))

    db.commit()

    return redirect('/kelola_produk')


# kelola resep produk
@app.route('/resep/<int:idProduk>')
def resep(idProduk):

    cursor = db.cursor()

    # ambil data produk
    cursor.execute("""
        SELECT *
        FROM produk
        WHERE idProduk = %s
    """, (idProduk,))

    produk = cursor.fetchone()

    # jika produk tidak ada
    if not produk:
        return "Produk tidak ditemukan"

    # ambil semua bahan baku
    cursor.execute("""
        SELECT *
        FROM bahanBaku
        ORDER BY namaBahan ASC
    """)

    bahan = cursor.fetchall()

    # ambil resep produk
    cursor.execute("""
        SELECT
            resep.idResep,
            bahanBaku.namaBahan,
            resep.jumlahPakai,
            bahanBaku.satuan

        FROM resep

        JOIN bahanBaku
        ON resep.idBahan = bahanBaku.idBahan

        WHERE resep.idProduk = %s
    """, (idProduk,))

    dataResep = cursor.fetchall()

    return render_template(
        'admin/resep.html',
        produk=produk,
        bahan=bahan,
        dataResep=dataResep
    )

@app.route('/tambah_resep', methods=['POST'])
def tambah_resep():

    idProduk = request.form['idProduk']
    idBahan = request.form['idBahan']
    jumlahPakai = request.form['jumlahPakai']

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO resep
        (
            idProduk,
            idBahan,
            jumlahPakai
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
    """, (
        idProduk,
        idBahan,
        jumlahPakai
    ))

    db.commit()

    return redirect('/resep/' + idProduk)

@app.route('/hapus_resep/<idResep>/<idProduk>')
def hapus_resep(idResep, idProduk):

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM resep
        WHERE idResep=%s
    """, (idResep,))

    db.commit()

    return redirect(f'/resep/{idProduk}')

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



# @app.route("/pembelian", methods=["GET", "POST"])
# def pembelian():

#     if request.method == "POST":

#         nama_barang = request.form["nama_barang"]
#         supplier = request.form["supplier"]

#         qty = float(
#             request.form["qty"]
#         )

#         satuan = request.form["satuan"]

#         tipe = request.form["tipe"]

#         harga_beli = int(
#             request.form["harga_beli"]
#         )


#         # ====================
#         # CONVERT SATUAN
#         # ====================

#         if satuan == "kg":

#             qty = qty * 1000
#             satuan = "gram"


#         elif satuan == "liter":

#             qty = qty * 1000
#             satuan = "ml"


#         subtotal = qty * harga_beli


#         # ====================
#         # HEADER PEMBELIAN
#         # ====================

#         pembelian_baru = Pembelian(

#             tanggal=date.today(),

#             total=subtotal,

#             namaSupplier=supplier,

#             idUser=session["idUser"]

#         )

#         db.session.add(
#             pembelian_baru
#         )

#         db.session.flush()


#         # ====================
#         # BARANG LANGSUNG
#         # ====================

#         if tipe == "langsung":

#             produk = produk.query.filter_by(

#                 namaProduk=nama_barang

#             ).first()


#             if not produk:

#                 return "Produk tidak ditemukan"


#             produk.stok += qty


#             detail = detailPembelian(

#                 idPembelian=
#                 pembelian_baru.idPembelian,

#                 idProduk=
#                 produk.idProduk,

#                 tipeBarang=
#                 "langsung",

#                 jumlah=
#                 qty,

#                 hargaBeli=
#                 harga_beli,

#                 subtotal=
#                 subtotal

#             )


#         # ====================
#         # BAHAN RACIKAN
#         # ====================

#         else:

#             bahan = bahanBaku.query.filter_by(

#                 namaBahan=nama_barang

#             ).first()


#             if not bahan:

#                 return "Bahan tidak ditemukan"


#             bahan.stok += qty


#             detail = detailPembelian(

#                 idPembelian=
#                 pembelian_baru.idPembelian,

#                 idBahan=
#                 bahan.idBahan,

#                 tipeBarang=
#                 "racikan",

#                 jumlah=
#                 qty,

#                 hargaBeli=
#                 harga_beli,

#                 subtotal=
#                 subtotal

#             )


#         db.session.add(
#             detail
#         )

#         db.session.commit()


#         return redirect(
#             "/pembelian"
#         )


# @app.route("/inventory")
# def inventory():

#     barang_langsung = produk.query.filter_by(
#         tipeProduk="langsung"
#     ).all()


#     bahan_racikan = bahanBaku.query.all()


#     return render_template(

#         "inventory.html",

#         barang_langsung=barang_langsung,

#         bahan_racikan=bahan_racikan

#     )

@app.route('/pembelian', methods=['GET', 'POST'])
def pembelian():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"

    cursor = db.cursor()

    if request.method == 'POST':

        namaBarang = request.form['nama_barang']
        supplier = request.form['supplier']
        qty = request.form['qty']
        satuan = request.form['satuan']
        tipe = request.form['tipe']

        # INSERT KE TABEL BAHAN BAKU
        cursor.execute("""
            INSERT INTO bahanbaku
            (
                namaBahan,
                stok,
                satuan,
                tipe
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            namaBarang,
            qty,
            satuan,
            tipe
        ))

        db.commit()

        return redirect('/pembelian')

    return render_template('admin/pembelian.html')

if __name__ == '__main__':
    app.run(debug=True)