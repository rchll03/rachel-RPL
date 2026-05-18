from datetime import date

from flask import Flask, render_template, request,redirect,session, url_for
import mysql.connector
import os

app = Flask(__name__,
            template_folder='../frontend',
            static_folder='../frontend/assets'
    )
app.secret_key = "kopiko123"
print("TEMPLATE:", app.template_folder)

# koneksi database
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="db_kopiko",
    auth_plugin='mysql_native_password',
    use_pure=True
)

cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

    # total transaksi
    cursor.execute("""
        SELECT COUNT(*)
        FROM transaksi
    """)
    totalTransaksi = cursor.fetchone()[0]

    # total pendapatan
    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM transaksi
    """)
    totalPendapatan = cursor.fetchone()[0]

    # total pembelian
    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM pembelian
    """)
    totalPembelian = cursor.fetchone()[0]

    # laporan transaksi terbaru
    cursor.execute("""
        SELECT
            idTransaksi,
            tanggal,
            total,
            bayar,
            kembalian
        FROM transaksi
        ORDER BY idTransaksi DESC
        LIMIT 5
    """)

    laporan = cursor.fetchall()

    return render_template(
        'owner/owner.html',
        totalTransaksi=totalTransaksi,
        totalPendapatan=totalPendapatan,
        totalPembelian=totalPembelian,
        laporan=laporan
    )


# pendapatan owner
@app.route('/pendapatan_owner')
def pendapatan_owner():

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM transaksi
    """)

    totalPendapatan = cursor.fetchone()[0]

    return render_template(
        'owner/pendapatan_owner.html',
        totalPendapatan=totalPendapatan
    )

# laporan owner
@app.route('/laporan_owner')
def laporan_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT
            idTransaksi,
            tanggal,
            total,
            bayar,
            kembalian
        FROM transaksi
        ORDER BY idTransaksi DESC
    """)

    laporan = cursor.fetchall()

    return render_template(
        'owner/laporan_owner.html',
        laporan=laporan
    )


# statistika owner
@app.route('/statistika_owner')
def statistika_owner():

    if 'idUser' not in session:
        return redirect('/')

    cursor = db.cursor(buffered=True)

    # total transaksi
    cursor.execute("SELECT COUNT(*) FROM transaksi")
    totalTransaksi = cursor.fetchone()[0]

    # total pembelian
    cursor.execute("SELECT COUNT(*) FROM pembelian")
    totalPembelian = cursor.fetchone()[0]

    # total pendapatan
    cursor.execute("SELECT IFNULL(SUM(total),0) FROM transaksi")
    totalPendapatan = cursor.fetchone()[0]

    # data grafik per bulan
    cursor.execute("""
        SELECT MONTH(tanggal), SUM(total)
        FROM transaksi
        GROUP BY MONTH(tanggal)
        ORDER BY MONTH(tanggal)
    """)

    data = cursor.fetchall()

    bulan = []
    pendapatan = []

    for x in data:
        bulan.append(str(x[0]))
        pendapatan.append(int(x[1]))

    return render_template(
        'owner/statistika_owner.html',
        totalTransaksi=totalTransaksi,
        totalPembelian=totalPembelian,
        totalPendapatan=totalPendapatan,
        bulan=bulan,
        pendapatan=pendapatan
    )


# pembelian owner
@app.route('/pembelian_owner')
def pembelian_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT *
        FROM pembelian
        ORDER BY idPembelian DESC
    """)

    pembelian = cursor.fetchall()

    return render_template(
        'owner/pembelian_owner.html',
        pembelian=pembelian
    )

    
# dashboard kasir
@app.route('/kasir')
def kasir():
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "kasir":
        return "Akses ditolak"
    
    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        DELETE FROM produk
        WHERE idProduk=%s
    """, (id,))

    db.commit()

    return redirect('/kelola_produk')


# kelola resep produk
@app.route('/resep/<int:idProduk>')
def resep(idProduk):

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        DELETE FROM resep
        WHERE idResep=%s
    """, (idResep,))

    db.commit()

    return redirect(f'/resep/{idProduk}')

# kelola user -- admin
@app.route('/kelola_user')
def kelola_user():

    cursor = db.cursor(buffered=True)

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


    cursor = db.cursor(buffered=True)


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

        cursor = db.cursor(buffered=True)

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

    cursor = db.cursor(buffered=True)

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

@app.route('/pembelian')
def pembelian():

    cursor = db.cursor(buffered=True)
    
    cursor.execute("""
        SELECT
            p.idPembelian,
            p.tanggal,
            p.namaSupplier,

            b.namaBahan,

            d.jumlah,
            d.hargaBeli,
            d.subtotal,

            p.total

        FROM pembelian p

        LEFT JOIN detailPembelian d
            ON p.idPembelian = d.idPembelian

        LEFT JOIN bahanBaku b
            ON d.idBahan = b.idBahan

        ORDER BY p.idPembelian DESC
    """)

    riwayat = cursor.fetchall()

    return render_template(
        'admin/pembelian.html',
        riwayat=riwayat
    )

@app.route('/simpan_pembelian', methods=['POST'])
def simpan_pembelian():

    cursor = db.cursor(buffered=True)

    tanggal = date.today()

    supplier = request.form['supplier']

    namaBarang = request.form.getlist('nama_barang[]')
    jumlah = request.form.getlist('jumlah[]')
    satuan = request.form.getlist('satuan[]')
    hargaBeli = request.form.getlist('harga_beli[]')

    total = 0

    # hitung total semua barang
    for i in range(len(namaBarang)):

        subtotal = int(jumlah[i]) * int(hargaBeli[i])

        total += subtotal

    # simpan tabel pembelian
    cursor.execute("""
        INSERT INTO pembelian
        (
            tanggal,
            total,
            namaSupplier
        )
        VALUES (%s,%s,%s)
    """, (
        tanggal,
        total,
        supplier
    ))

    idPembelian = cursor.lastrowid

    # simpan detail pembelian
    for i in range(len(namaBarang)):

        subtotal = int(jumlah[i]) * int(hargaBeli[i])

        # cek bahan baku
        cursor.execute("""
            SELECT idBahan
            FROM bahanBaku
            WHERE namaBahan = %s
        """, (namaBarang[i],))

        bahan = cursor.fetchone()

        # jika belum ada bahan baku
        if bahan is None:

            cursor.execute("""
                INSERT INTO bahanBaku
                (
                    namaBahan,
                    stok,
                    satuan
                )
                VALUES (%s,%s,%s)
            """, (
                namaBarang[i],
                jumlah[i],
                satuan[i]
            ))

            idBahan = cursor.lastrowid

        else:

            idBahan = bahan[0]

            # update stok
            cursor.execute("""
                UPDATE bahanBaku
                SET stok = stok + %s
                WHERE idBahan = %s
            """, (
                jumlah[i],
                idBahan
            ))

        # simpan detail
        cursor.execute("""
            INSERT INTO detailPembelian
            (
                idPembelian,
                idBahan,
                jumlah,
                hargaBeli,
                subtotal
            )
            VALUES (%s,%s,%s,%s,%s)
        """, (
            idPembelian,
            idBahan,
            jumlah[i],
            hargaBeli[i],
            subtotal
        ))

    db.commit()

    return redirect('/pembelian')

@app.route('/hapus_pembelian/<id>')
def hapus_pembelian(id):

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        DELETE FROM pembelian
        WHERE idPembelian = %s
    """, (id,))

    db.commit()

    return redirect('admin/pembelian')

@app.route('/edit_pembelian/<id>', methods=['POST'])
def edit_pembelian(id):

    cursor = db.cursor(buffered=True)

    namaSupplier = request.form['namaSupplier']
    namaBarang = request.form['namaBarang']
    jumlah = int(request.form['jumlah'])
    hargaBeli = int(request.form['hargaBeli'])

    subtotal = jumlah * hargaBeli
    total = subtotal

    # update pembelian
    cursor.execute("""
        UPDATE pembelian
        SET
            namaSupplier = %s,
            total = %s
        WHERE idPembelian = %s
    """, (
        namaSupplier,
        total,
        id
    ))

    # update detail
    cursor.execute("""
        UPDATE detailpembelian
        SET
            idBahan = %s,
            jumlah = %s,
            hargaBeli = %sS,
            subtotal = %s
        WHERE idPembelian = %s
    """, (
        namaBarang,
        jumlah,
        hargaBeli,
        subtotal,
        id
    ))

    db.commit()

    return redirect('admin/pembelian')


if __name__ == '__main__':
    app.run(debug=True)

