import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123",
    database="db_kopiko v1"
)

print("Koneksi berhasil!")