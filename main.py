from flask import Flask, render_template, request, redirect, url_for, session
import os
import re
#from bs4 import BeautifulSoup
import requests
from advertools import crawl
import pandas as pd
from waitress import serve

app = Flask(__name__)
 
#app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
H1_NOT = []
STATUS_CODE_BAD=[]
H1_DUPLICATE = []
DF = None

@app.route('/') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def index(): #ana sayfayı render eder 
    return render_template('index.html') #html sayfası oluşturan fonksiyon render_template

@app.route('/anasayfa') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def anasayfa(): #ana sayfayı render eder 
    return render_template('index.html') #html sayfası oluşturan fonksiyon render_template



def create_jl_file(url, jl_file_name):
    crawl(url, jl_file_name, follow_links=True, custom_settings={'DOWNLOAD_DELAY': 1})

def read_df_from_jl(jl_file_name):
    return pd.read_json(jl_file_name, lines=True)


def clear_lists():
    global H1_NOT, STATUS_CODE_BAD, H1_DUPLICATE
    H1_NOT = []
    STATUS_CODE_BAD = []
    H1_DUPLICATE = []


#crawl(url, output_file, follow_links=True, custom_settings={'DOWNLOAD_DELAY': 1})
#df = pd.read_json(output_file, lines=True)
#htmlOut = df.to_html(f"{url.replace('http://', '').replace('https://', '').replace('/', '').replace('.com', '')}.html")     
#return htmlOut is not None



def SEOTestOnem(onem, fonkParamatre):
    dereceler = {
        'kritik':[[H1_NOT]],
        'uyari':[[STATUS_CODE_BAD]],
        'bilgilendirme':[[H1_DUPLICATE]]
    }
    return fonkParamatre in dereceler.get(onem, [])


def SEOtest(fonkParametre):
    def decorator(func):
        def wrapper(onem):
            if SEOTestOnem(onem, fonkParametre):
                func(onem)
            else:
                return "yanlış aksiyon"
        return wrapper
    return decorator



@SEOtest([H1_NOT])
def h1Avaliable(onem):
    for idx, row in DF.iterrows(): #iterrows satır bazında iterasyon sağlar. idx index i verir. dinamiklik sağlar.
        if pd.isna(row["h1"]):
            H1_NOT.append(row["url"])
    #print(f"H1 başlığı bulunmayanlar : {H1_NOT}")
    return H1_NOT

@SEOtest([STATUS_CODE_BAD])
def badStatus(onem):
        for idx, row in DF.iterrows():
            status_str = str(row["status"]) #kıyaslama için str haline getirildi.
            if re.match(r'^4\d{2}$', status_str): #durum kodunun 4xx olduğunu test etmek için yazılmıştır.
                STATUS_CODE_BAD.append(row["url"])
            #print(f"4xx durum koduna sahip linkler: {STATUS_CODE_BAD}")
            return STATUS_CODE_BAD

@SEOtest([H1_DUPLICATE])
def duplicateH1(onem):
        for idx, row in DF.iterrows():
            h1InValue =  str(row["h1"])
            if "@@" in h1InValue:
                H1_DUPLICATE.append(row["url"])
            #print(f"H1 satırı birden fazla kez kullanılmış olan adresler: {H1_DUPLICATE}"
            return H1_DUPLICATE
 


#@app.route('/webCrawler', methods=['POST'])
#def webCrawl():
    #h1Avaliable("kritik")
    #badStatus("uyari")
    #duplicateH1("bilgilendirme")
    #return render_template('webCrawl.html', kritik=H1_NOT, uyari=STATUS_CODE_BAD, bilgilendirme=H1_DUPLICATE)

@app.route('/webCrawler', methods=['POST'])
def webCrawlerFromForm():
    global DF

    url = request.form.get('url')

    if not url:
        return "URL girilmedi"

    jl_file_name = f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}_output.jl"

    create_jl_file(url, jl_file_name)# 1. Adım: .jl dosyası oluşturuldu
    DF = read_df_from_jl(jl_file_name) # 2. Adım: .jl dosyasını okuyarak DataFrame oluşturuluyor
    clear_lists()
    h1Avaliable("kritik") # Diğer SEO test fonksiyonlarını çağırmaktadır
    badStatus("uyari")
    duplicateH1("bilgilendirme")

    # HTML şablonuna sonuçları gönder
    return render_template('webCrawl.html', kritik=H1_NOT, uyari=STATUS_CODE_BAD, bilgilendirme=H1_DUPLICATE)


if __name__ == '__main__':
   
    serve(app, host='0.0.0.0', port=5000)
    app.debug=False
    #app.run(debug=False)