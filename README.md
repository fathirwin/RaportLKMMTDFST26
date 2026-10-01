# Raport LKMM TD FST Unair 2026

Website cek raport berbasis Flask (Python), dengan HTML (Jinja2).

## Struktur File
```
raport-lkmm-td/
├── app.py
├── data.py
├── db.py                
├── requirements.txt     
├── .env                 
├── .gitignore           
├── sql/schema.sql       
├── static/
|    ├── style.css
|    └── image/logo-bem.png    
└── templates/
    ├── _flash.html         
    ├── index.html
    ├── raport.html
    ├── admin_login.html    
    ├── admin_dashboard.html 
    ├── admin_form.html     
    └── error.html          
```

## Cara Menjalankan (Lokal)
```bash
pip install flask
python app.py
```
Buka `http://127.0.0.1:5000` di browser. Coba NIM contoh: `187241054` (belum final) atau `187241103` (sudah final).
