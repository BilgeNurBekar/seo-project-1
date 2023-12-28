from flask import Flask, render_template, request
import re
import os
from advertools import crawl
import advertools as adv
import pandas as pd
from waitress import serve

app = Flask(__name__)
 


@app.route('/') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def index(): #ana sayfayı render eder 
    return render_template('index.html') #html sayfası oluşturan fonksiyon render_template

@app.route('/anasayfa') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def anasayfa(): #ana sayfayı render eder 
    return render_template('index.html') #html sayfası oluşturan fonksiyon render_template



def create_jl_file(url, jl_file_name):
    crawl(url, jl_file_name, follow_links=True, custom_settings={'DOWNLOAD_DELAY': 1})

def read_df_from_jl(jl_file_name):
    #return pd.read_json(jl_file_name, lines=True)
    try:
        df = pd.read_json(jl_file_name, lines=True)
        return df
    except ValueError as e:
        print(f"Hata: JSON dosyasını okuma sırasında bir sorun oluştu: {e}")
        return None


def deleteFile(jl_file_name):
    #with open(jl_file_name, 'w') as dosya:
    #   dosya.write('')
    try:
        os.remove(jl_file_name)
        print(f"{jl_file_name} dosyası silindi.")
    except FileNotFoundError:
        print(f"{jl_file_name} dosyası bulunamadı.")
    except PermissionError:
        print(f"{jl_file_name} dosyasını silme izinleri yok.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")


#def clear_lists():
#    global H1_NOT, STATUS_CODE_4xx, H1_DUPLICATE, load_times,STATUS_CODE_BAD,DESCRIPTION_META, DESCRIPTION_EMPTY,TITLE_EMPTY,DESCRIPTION_LONG, DESCRIPTION_SHORT,CANONICAL_NOT,IMG_ALT_NOT,ROBOTS_TXT_DISALLOW,robotsIsNot,IMG_ALT_EMPTY,canonicInfo
#    H1_NOT = []
#    STATUS_CODE_4xx = []
#    H1_DUPLICATE = []
#    STATUS_CODE_BAD = []
#    load_times = []
#    DESCRIPTION_META = []
#    DESCRIPTION_EMPTY = []
#    TITLE_EMPTY = []
#    DESCRIPTION_LONG = []
#    DESCRIPTION_SHORT = []
#    CANONICAL_NOT = []
#    IMG_ALT_NOT = []
#    ROBOTS_TXT_DISALLOW = []
#    robotsIsNot = None
#    IMG_ALT_EMPTY = []
#    canonicInfo = ""
    
#crawl(url, output_file, follow_links=True, custom_settings={'DOWNLOAD_DELAY': 1})
#df = pd.read_json(output_file, lines=True)
#htmlOut = df.to_html(f"{url.replace('http://', '').replace('https://', '').replace('/', '').replace('.com', '')}.html")     
#return htmlOut is not None


#def SEOTestOnem(onem, fonkParamatre):
#    dereceler = {
#        'kritik':[[H1_NOT],[STATUS_CODE_BAD],[DESCRIPTION_EMPTY],[TITLE_EMPTY],[IMG_ALT_NOT],[IMG_ALT_EMPTY]],
#        'uyari':[[STATUS_CODE_4xx],[load_times],[H1_DUPLICATE],[ROBOTS_TXT_DISALLOW],robotsIsNot],
#        'bilgilendirme':[[DESCRIPTION_LONG],[DESCRIPTION_SHORT],[CANONICAL_NOT],canonicInfo]
#    }
#    return fonkParamatre in dereceler.get(onem, [])


#def SEOtest(fonkParametre):
#    def decorator(func):
#        def wrapper(onem):
#            if SEOTestOnem(onem, fonkParametre):
#                func(onem)
#            else:
#                return "yanlış aksiyon"
#        return wrapper
#    return decorator


def h1Avaliable(H1_NOT,DF,temp):
    for idx, row in DF.iterrows(): #iterrows satır bazında iterasyon sağlar. idx index i verir. dinamiklik sağlar.
        if pd.isna(row["h1"]):
            temp.append(row["url"])
    H1_NOT = set(temp)
    if not H1_NOT:
        return "Harika H1 etiketi kullanılmayan sayfaya rastlanmadı :)"
    else: 
        return H1_NOT


def clientError(STATUS_CODE_4xx,DF, temp):
    for idx, row in DF.iterrows():
        status_str = str(row["status"]) #kıyaslama için str haline getirildi.
        if re.match(r'^4\d{2}$', status_str): #durum kodunun 4xx olduğunu test etmek için yazılmıştır.
            temp.append(row["url"])
    STATUS_CODE_4xx = set(temp)
    if not STATUS_CODE_4xx:
        return "Harika sayfalarda 4xx durum koduna rastlanmadı :)"
    else:
        #print(f"4xx durum koduna sahip linkler: {STATUS_CODE_BAD}")
        return STATUS_CODE_4xx


def duplicateH1(H1_DUPLICATE,DF,temp):
    for idx, row in DF.iterrows():
        h1InValue =  str(row["h1"])
        if "@@" in h1InValue:
            temp.append(row["url"])
    H1_DUPLICATE = set(temp)
    if not H1_DUPLICATE:
        return "Harika bir sayfada birden fazla H1 etiketi kullanan adres bulunmadı :)"
         #print(f"H1 satırı birden fazla kez kullanılmış olan adresler: {H1_DUPLICATE}"
    return H1_DUPLICATE


def badStatus(STATUS_CODE_BAD,DF,temp):
    for idx, row in DF.iterrows():
        badCode =  str(row["status"])
        if badCode =='404':
            temp.append(row["url"])
    STATUS_CODE_BAD = set(temp)
    if not STATUS_CODE_BAD:
        return "Harika 404 durum koduna sahip sayfaya rastlanmadı :)"
    else:        
        return STATUS_CODE_BAD
        

def pageOpeningTime(load_times,DF, temp):
    try:
        for idx, row in DF.iterrows():
            time = row["download_latency"]
            if time > 3:
                temp.append(row["url"])
        load_times = set(temp)
        if not load_times:
            return "Harika web sayfaların 3 sn gibi kısa bir süreden dahi hızlı açılmakta :)"
        else:
            return load_times
    except Exception as e:
        return str(e) 



def duplicateMeta(DESCRIPTION_META,DF,temp):
    non_nan_mask = ~DF["meta_desc"].isna() #~ ile NaN olmayan değerler seçilir.
    filtered_df = DF[non_nan_mask]

    for idx, row in filtered_df.iterrows():
    # Burada işlemlerinizi gerçekleştirin
    # DESCRIPTION_META listesine URL ekleyin
        DESCRIPTION_META.append(row["url"])
    return set(DESCRIPTION_META)


 #meta description olup olmadığını test eder 
def descriptionMissing(DESCRIPTION_EMPTY,DF,temp):
    for idx, row in DF.iterrows():
        if pd.isna(row["meta_desc"]):
            temp.append(row["url"])
    DESCRIPTION_EMPTY = set(temp)
    if not DESCRIPTION_EMPTY:
        return "Harika meta description'a sahip olmayan bir adres ile karşılaşılmadı :) "
    else: 
        return DESCRIPTION_EMPTY


 #title tag ının olup olmadığını kontrol eder      
def titleEmpty(TITLE_EMPTY,DF,temp):
    for idx, row in DF.iterrows():
        if pd.isna(row["title"]):
            temp.append(row["url"])
    TITLE_EMPTY = set(temp)
    if not TITLE_EMPTY:
        return "Harika title etiketine sahip olmayan bir sayfa bulunmadı :)"
    else: 
        return TITLE_EMPTY



def longDesc(DESCRIPTION_LONG,DF,temp):  #description' ın uzunluğunu test eder
    for idx, row in DF.iterrows():
        boyut = str(row["meta_desc"])
        if len(boyut)>160:
            temp.append(row["url"])
    DESCRIPTION_LONG = set(temp)
    if not DESCRIPTION_LONG:
        return "Harika tüm adreslerde meta açıklamaların uzun bulunmadı :) "
    return DESCRIPTION_LONG



def shortDesc(DESCRIPTION_SHORT,DF,temp):  #description' ın uzunluğunu test eder
    for idx, row in DF.iterrows():
        boyut = str(row["meta_desc"])
        if len(boyut)<50:
            temp.append(row["url"])
    DESCRIPTION_SHORT = set(temp)
    if not DESCRIPTION_SHORT: 
        return "Harika tüm adreslerde meta açıklamanın uzunluğu kısa değil :)"
    else:
        return DESCRIPTION_SHORT


#@SEOtest([CANONICAL_NOT] or canonicInfo) #canonic url kullanılmayan adresleri tespit eder
def canonicalMissing(CANONICAL_NOT,canonicInfo,DF,temp):
    if "canonical" in DF.columns:
        for idx, row in DF.iterrows():
            if pd.isna(row["canonical"]):
                temp.append(row["url"])
        CANONICAL_NOT = set(temp)
        if not CANONICAL_NOT:
            return "Harika kanonik etikete adreslerde yer verilmiş :)"
        else:
            return CANONICAL_NOT 
    else:
        canonicInfo = "canonical hakkında bilgi alınamadı etiket hiç bulunmayabilir."
        return canonicInfo

 #img alt tagında açıklaması eksik olan adresleri verir
def imgAltNot(IMG_ALT_NOT,DF, temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["img_src"]):
            img_alt_value = row["img_alt"]
            if pd.isna(img_alt_value):
                temp.append(row["url"])
    IMG_ALT_NOT = set(temp)
    if not IMG_ALT_NOT:
        return "Harika IMG açıklmalarına tüm adreslerde yer verilmiş :)"
    return set(IMG_ALT_NOT)



def imgAltEmpty(IMG_ALT_EMPTY,DF, temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["img_src"]):
            img_alt = str(row["img_alt"])
            if "@@@" in img_alt:
                temp.append(row["url"])
    IMG_ALT_EMPTY = set(temp)
    if not IMG_ALT_EMPTY:
        return "Harika img açıklamaları tüm adreslerde dolu görünüyor :)"
    return IMG_ALT_EMPTY

# fonksiyonlar nan yada değer döndürürp boş olabilir bunu göz önünde bulunurup kodu ona göre yazman lazım. 
#nan ise mesela zaten ölçmeye gerek yok 
#@@@ ise ancak o zaman urlleri doldurur



def disallowRobots(ROBOTS_TXT_DISALLOW,robotsIsNot,temp):
    url = request.form.get("url")
    url = url.split("//")
    domainUrl = url[0] + "//" + url[1].split("/")[0]
    robotsUrl = domainUrl + "/robots.txt"
    robotsFile = adv.robotstxt_to_df(robotsUrl) #robots.txt uzantısı dataframe haline getirilidi
    if robotsFile is None: 
        return robotsIsNot
    for idx, row in robotsFile.iterrows():
        if "Disallow" in row["directive"]:
            if "/" in row["content"]:
                addr = domainUrl + row["content"]
                temp.append(addr)
    ROBOTS_TXT_DISALLOW = set(temp)
    if len(ROBOTS_TXT_DISALLOW) == 0:
        return "Robots.txt 'nin erişimi engelleyen bir adresi bulunmadı"
    return ROBOTS_TXT_DISALLOW

def redirectImage(REDIRECT_IMG_URL,DF,temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["img_src"]):
            img_srcc = str(row["img_src"])
            if "http" in img_srcc:
                temp.append(row["url"])
    REDIRECT_IMG_URL = set(temp)
    if not REDIRECT_IMG_URL:
        return "Harika img etiketlerinde bir web adresinden kaynak bulunmadı :)"
    return REDIRECT_IMG_URL


def serverErrors(STATUS_CODE_5XX, DF,temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["status"]):
            status5xx = str(row["status"])
            if re.match(r'^5\d{2}$', status5xx): #durum kodunun 5xx olduğunu test etmek için yazılmıştır.
                temp.append(row["url"])
        else:
            return "Durum kodu bilgisine ulaşılamadı. Daha sonra tekrar deneyiniz."
    STATUS_CODE_5XX = set(temp)
    if not STATUS_CODE_5XX:
        return "Harika sayfalarda 5xx server error' a rastlanmadı :)"
    else:
        return STATUS_CODE_5XX
    
def movedPermanently(STATUS_CODE_301,DF, temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["status"]):
            status301 = str(row["status"])
            if status301 == "301": #durum kodunun 301 olduğunu test etmek için yazılmıştır.
                temp.append(row["url"])
        else:
            return "Durum kodu bilgisine ulaşılamadı. Daha sonra tekrar deneyiniz."
    STATUS_CODE_301 = set(temp)
    if not STATUS_CODE_301:
        return "Harika sayfalarda 301 kaynak kalıcı olarak taşındı durum koduna rastlanmadı :)"
    else:
        return STATUS_CODE_301
    
def movedTemporarily(STATUs_CODE_302,DF, temp):
    for idx, row in DF.iterrows():
        if pd.notna(row["status"]):
            status302 = str(row["status"])
            if status302 == "302": #durum kodunun 302 olduğunu test etmek için yazılmıştır.
                temp.append(row["url"])
        else:
            return "Durum kodu bilgisine ulaşılamadı. Daha sonra tekrar deneyiniz."
    STATUS_CODE_302 = set(temp)
    if not STATUS_CODE_302:
        return "Harika sayfalarda 302 kaynak geçici olarak taşındı durum koduna rastlanmadı :)"
    else:
        return STATUS_CODE_302

@app.route('/webCrawler', methods=['POST', 'GET'])
def webCrawlerFromForm():
    if request.method == "POST":
        url = request.form.get('url')

        if not url:
            return "URL girilmedi"

        jl_file_name = f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}_output.jl"
        test_sonuc = "TEST SONUÇLARI" #webCrawler.html için oluşturulan eğer sayfa taranmmışsa dönen değişken
        create_jl_file(url, jl_file_name)# 1. Adım: .jl dosyası oluşturuldu
        DF = read_df_from_jl(jl_file_name)# 2. Adım: .jl dosyasını okuyarak DataFrame oluşturuluyor
        IMG_ALT_EMPTY = []
        IMG_ALT_NOT = []
        ROBOTS_TXT_DISALLOW = []
        temp =[] 
        canonicInfo = None
        robotsIsNot = "Robots.txt dosyası bulunamadı"
        DESCRIPTION_SHORT = []
        DESCRIPTION_LONG = []
        CANONICAL_NOT =[]
        canonicInfo = ""
        load_times = []
        H1_NOT = []
        STATUS_CODE_4xx = []
        H1_DUPLICATE = []
        STATUS_CODE_BAD=[]
        DESCRIPTION_META = []
        DESCRIPTION_EMPTY = []
        TITLE_EMPTY = []
        REDIRECT_IMG_URL = []
        STATUS_CODE_5XX = []
        STATUS_CODE_301 = []
        STATUS_CODE_302 = []
        #clear_lists()
        print(DF.columns)
        # HTML şablonuna sonuçları gönder
        #htmlOut = DF.to_html(f"{url.replace('http://', '').replace('https://', '').replace('/', '').replace('.com', '')}.html")
        deleteFile(jl_file_name)
        
        return render_template('webCrawl.html', test_sonuc1=test_sonuc, h1isnot=h1Avaliable(H1_NOT, DF,temp=[]),badstatus=badStatus(STATUS_CODE_BAD, DF,temp=[]), status4xx=clientError(STATUS_CODE_4xx,DF, temp=[]),
                                h1duplicate=duplicateH1(H1_DUPLICATE,DF, temp=[]),
                               time=pageOpeningTime(load_times,DF, temp=[]),duplicatedmeta=duplicateMeta(DESCRIPTION_META, DF,temp=[]),emptyDescription=descriptionMissing(DESCRIPTION_EMPTY,DF,temp=[]), 
                               notTitle=titleEmpty(TITLE_EMPTY, DF,temp=[]), descLong = longDesc(DESCRIPTION_LONG,DF,temp=[]), descShort =shortDesc(DESCRIPTION_SHORT,DF,temp=[]),
                               notcanonic=canonicalMissing(CANONICAL_NOT,canonicInfo,DF,temp=[]),imgAltNot=imgAltNot(IMG_ALT_NOT,DF, temp=[]), 
                               imgAltEmpty=imgAltEmpty(IMG_ALT_EMPTY,DF,temp=[]),robots =disallowRobots(ROBOTS_TXT_DISALLOW,robotsIsNot,temp=[]), redirectImg=redirectImage(REDIRECT_IMG_URL,DF,temp)
                               ,status5xx = serverErrors(STATUS_CODE_5XX,DF,temp=[]), status301=movedPermanently(STATUS_CODE_301,DF, temp=[]), status302 = movedTemporarily(STATUS_CODE_302,DF,temp=[]))
    else:
        test_sonuc= "Upps Sanırım Tarama Henüz Yapılmamış"
        return render_template('webCrawl.html', test_sonuc2=test_sonuc)

if __name__ == '__main__':
   
    serve(app, host='0.0.0.0', port=5000)
    app.debug=False
   

