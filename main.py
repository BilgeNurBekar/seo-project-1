from flask import Flask, render_template, request,redirect, url_for, send_from_directory
import re
import os
from advertools import crawl
import advertools as adv
import pandas as pd
from waitress import serve
from urllib.parse import urlparse, urljoin
import time 
from werkzeug.utils import secure_filename


app = Flask(__name__)
 

urlList = []

@app.route('/') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def index(): #ana sayfayı render eder
    return render_template('anasayfa.html') #html sayfası oluşturan fonksiyon render_template

@app.route('/anasayfa') #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def anasayfa(): #ana sayfayı render eder 
    return render_template('anasayfa.html') #html sayfası oluşturan fonksiyon render_template

@app.route('/file', methods=['GET']) #decorator kullanmış buna göre olmasını istiyorsan yap demektir. bu kullanım 
def file(): #ana sayfayı render eder 
        return render_template('fileUpload.html') #html sayfası oluşturan fonksiyon render_template


def isValidUrl(url, jl_file_name):
    try:
        urlResult = urlparse(url)
        if all([urlResult.scheme, urlResult.netloc]): #url formatını kontrol eder
            urlFormat = "Url formatınız doğru. Tarama başlatılıyor"
            startTime = time.time()
            create_jl_file(url, jl_file_name)
            df = read_df_from_jl(jl_file_name)
            if "errors" not in df.columns: #eger errors satırı varsa web de olmayan bir url adresi denenmiş demektir.
                return urlFormat, True , df ,startTime
            else:
                urlFormat = "Böyle bir adres bulunamadı. Başka adresi yeniden deneyiniz"
                startTime = None
                return urlFormat, False ,df,startTime
        else:
            urlFormat = "url formatına uygun bir adres girilmedi lütfen yeniden deneyin!"
            startTime = None
            df = None
            return urlFormat, False ,df, startTime
    except Exception as e:
        return f"Hata: {str(e)}",False,df, None


def create_jl_file(url, jl_file_name):
    crawl(url, jl_file_name, follow_links=True, custom_settings={'DOWNLOAD_DELAY': 1})

def read_df_from_jl(jl_file_name):
    try:
        df = pd.read_json(jl_file_name, lines=True)
        return df
    except ValueError as e:
        print(f"Hata: JSON dosyasını okuma sırasında bir sorun oluştu: {e}")
        return None
    

def deleteFile(jl_file_name):
    try:
        os.remove(jl_file_name)
        print(f"{jl_file_name} dosyası silindi.")
    except FileNotFoundError:
        print(f"{jl_file_name} dosyası bulunamadı.")
    except PermissionError:
        print(f"{jl_file_name} dosyasını silme izinleri yok.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")



ALLOWED_EXTENSIONS = {'html'} #izin verilen dosya uzantıları
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
UPLOAD_FOLDER = 'static/' #yüklenen ddosyaların saklanacağı yer 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAX_FILES_ALLOWED = 5  #yükleneblecek max dosya sayısı

def deleteHtmlFiles(): #yüklenen dosyalar tarama işleminin ardından silinir
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if filename.endswith(".html") and os.path.isfile(file_path):
                os.remove(file_path)
        print(f"{app.config['UPLOAD_FOLDER']} klasörü içindeki .html uzantılı dosyalar silindi.")
    except FileNotFoundError:
        print(f"{app.config['UPLOAD_FOLDER']} klasörü bulunamadı.")
    except PermissionError:
        print(f"{app.config['UPLOAD_FOLDER']} klasörünü silme izinleri yok.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

@app.route('/file', methods=['POST','GET'])
def uploadFile():
    if request.method=="POST":
        if 'dosya[]' in request.files:
            files = request.files.getlist('dosya[]') #birden fazla yüklemeyi kontrol eder.
            if len(files) > MAX_FILES_ALLOWED:
                labelFileCount = "En fazla 5 adet dosya yüklenebilir"
                return render_template ("fileUpload.html", labelFileCount = labelFileCount)

            for file in files:
                if file and allowedFile(file.filename): 
                    filename = secure_filename(file.filename)
                    try:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                    except Exception as e:
                        return render_template("fileUpload.html", labelFileCount=str(e))
                if file and not allowedFile(file.filename):
                    return redirect(url_for('error_404'))
            global urlList
            urlList = [urljoin(request.url_root, f'html_files/{secure_filename(file.filename)}') for file in files]  #yüklenen dosyalar url formatına dönüştürüldü
            print("***********************")
            print("Dosya URL'leri:", urlList)
            print("***********************")
            labelFileCount = "Yükleme Başarılı. Taramayı Başlatın" 
            return render_template("fileUpload.html", labelFileCount = labelFileCount)
        return 'File Upload failed'
        
    else:
        test_sonuc2= "Daha sonra tarama işlemi için dosya yükleyiniz. "
        return render_template("fileCrawl.html", test_sonuc2=test_sonuc2)

def allowedFile(filename): #izin verilen dosya formatını kontrol eder
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/html_files/<path:page_name>') #sayfaların yayınlanacağı uzantı
def serve_page(page_name):
    # Yüklenen HTML sayfalarını sunmak için bu endpoint'i kullanın
    return send_from_directory(app.config['UPLOAD_FOLDER'], page_name)


def createForFile(urlList,jl_file_name): #yüklenen fileların taranması için liste tabanlı tarama 
    crawl(urlList, jl_file_name, follow_links=False)

@app.route("/file/crawl", methods=['POST', 'GET'])
def fileCrawler():
    if request.method =='POST':
        global urlList 
        test_sonuc = "TEST SONUÇLARI" #webCrawler.html için oluşturulan eğer sayfa taranmmışsa dönen değişken
        jl_file_name = "temp.jl"         
        startTime = time.time()
        createForFile(urlList,jl_file_name)# 1. Adım: .jl dosyası oluşturuldu
        df = read_df_from_jl(jl_file_name)# 2. Adım: .jl dosyasını okuyarak DataFrame oluşturuluyor
        if df is not None and not df.empty:
            IMG_ALT_EMPTY = []
            IMG_ALT_NOT = []
            temp =[] 
            canonicInfo = None
            DESCRIPTION_SHORT = []
            DESCRIPTION_LONG = []
            CANONICAL_NOT =[]
            canonicInfo = ""
            titleInfo = ""
            load_times = []
            H1_NOT = []
            h1Info =""
            descInfo = ""
            imgInfo = ""
            STATUS_CODE_4xx = []
            H1_DUPLICATE = []
            STATUS_CODE_BAD=[]
            DESCRIPTION_EMPTY = []
            TITLE_EMPTY = []
            REDIRECT_IMG_URL = []
            STATUS_CODE_5XX = []
            STATUS_CODE_301 = []
            STATUS_CODE_302 = []
            endTime = time.time()
            crawlingTime = endTime - startTime
            hours, minutes, seconds = formatTime(crawlingTime) # tarama süresini saat dakika saniye olarak verir
            print(df.columns)
            deleteFile(jl_file_name)
            deleteHtmlFiles()       
            if df is not None and not df.empty:
            
            
            # HTML çıktısı alınabilir kontrol amaçlı
            #    html_output = df.to_html(f"deneme.html")
       
                return render_template('fileCrawl.html', test_sonuc1=test_sonuc, h1isnot=h1Avaliable(H1_NOT,h1Info, df,temp=[]),badstatus=badStatus(STATUS_CODE_BAD, df,temp=[]), status4xx=clientError(STATUS_CODE_4xx,df, temp=[]),
                                                h1duplicate=duplicateH1(H1_DUPLICATE,h1Info,df, temp=[]),
                                            time=pageOpeningTime(load_times,df, temp=[]),emptyDescription=descriptionMissing(DESCRIPTION_EMPTY,descInfo,df,temp=[]), 
                                            notTitle=titleEmpty(TITLE_EMPTY,titleInfo, df,temp=[]), descLong = longDesc(DESCRIPTION_LONG,descInfo,df,temp=[]), descShort =shortDesc(DESCRIPTION_SHORT,descInfo, df,temp=[]),
                                            notcanonic=canonicalMissing(CANONICAL_NOT,canonicInfo,df,temp=[]),imgAltNot=imgAltNot(IMG_ALT_NOT,imgInfo,df, temp=[]), 
                                            imgAltEmpty=imgAltEmpty(IMG_ALT_EMPTY,imgInfo,df,temp=[]), redirectImg=redirectImage(REDIRECT_IMG_URL,imgInfo,df,temp)
                                            ,status5xx = serverErrors(STATUS_CODE_5XX,df,temp=[]), status301=movedPermanently(STATUS_CODE_301,df, temp=[]), status302 = movedTemporarily(STATUS_CODE_302,df,temp=[]),
                                                crawltime=f"{hours:02d}h {minutes:02d}m {seconds:.0f}s")
    else:
        test_sonuc2= "Daha sonra tarama işlemi için dosya yükleyiniz. "
        return render_template("fileCrawl.html", test_sonuc2=test_sonuc2)

        


def h1Avaliable(H1_NOT,h1Info,df,temp):
    try:
        if "h1" in df.columns:
            for idx, row in df.iterrows(): #iterrows satır bazında iterasyon sağlar. idx index i verir. dinamiklik sağlar.
                if pd.isna(row["h1"]):
                    temp.append(row["url"])
            H1_NOT = set(temp)
            if not H1_NOT:
                return "Harika H1 etiketi kullanılmayan sayfaya rastlanmadı :)"
            else: 
                return H1_NOT
        else:
            h1Info = "H1 etiketi hakkında bilgi alınamadı. H1 etiketi kullanılmamış."
            return h1Info
    except Exception as e:
        return str(e) 


def clientError(STATUS_CODE_4xx,df, temp):
    try:
        for idx, row in df.iterrows():
            status_str = str(row["status"]) #kıyaslama için str haline getirildi.
            if re.match(r'^4\d{2}$', status_str): #durum kodunun 4xx olduğunu test etmek için yazılmıştır.
                temp.append(row["url"])
        STATUS_CODE_4xx = set(temp)
        if not STATUS_CODE_4xx:
            return "Harika sayfalarda 4xx durum koduna rastlanmadı :)"
        else:
            #print(f"4xx durum koduna sahip linkler: {STATUS_CODE_BAD}")
            return STATUS_CODE_4xx
    except Exception as e:
        return str(e) 


def duplicateH1(H1_DUPLICATE,h1Info, df,temp):
    try:
        if "h1" in df.columns:
            for idx, row in df.iterrows():
                h1InValue =  str(row["h1"])
                if "@@" in h1InValue:
                    temp.append(row["url"])
            H1_DUPLICATE = set(temp)
            if not H1_DUPLICATE:
                return "Harika bir sayfada birden fazla H1 etiketi kullanan adres bulunmadı :)"
                #print(f"H1 satırı birden fazla kez kullanılmış olan adresler: {H1_DUPLICATE}"
            return H1_DUPLICATE
        else:
            h1Info = "H1 etiketi hakkında bilgi yok/ H1 etiketi kullanılmamış."
            return h1Info
    except Exception as e:
        return str(e) 

def badStatus(STATUS_CODE_BAD,df,temp):
    try:
        for idx, row in df.iterrows():
            badCode =  str(row["status"])
            if badCode =='404':
                temp.append(row["url"])
        STATUS_CODE_BAD = set(temp)
        if not STATUS_CODE_BAD:
            return "Harika 404 durum koduna sahip sayfaya rastlanmadı :)"
        else:        
            return STATUS_CODE_BAD
    except Exception as e:
        return str(e) 

def pageOpeningTime(load_times,df, temp):
    try:
        for idx, row in df.iterrows():
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



def duplicateMeta(DESCRIPTION_META,df,temp):
    try:
        non_nan_mask = ~df["meta_desc"].isna() #~ ile NaN olmayan değerler seçilir.
        filtered_df = df[non_nan_mask]

        for idx, row in filtered_df.iterrows():
        # Burada işlemlerinizi gerçekleştirin
        # DESCRIPTION_META listesine URL ekleyin
            DESCRIPTION_META.append(row["url"])
        return set(DESCRIPTION_META)
    except Exception as e:
        return str(e) 


 #meta description olup olmadığını test eder 
def descriptionMissing(DESCRIPTION_EMPTY,descInfo,df,temp):
    try:
        if "meta_desc" in df.columns:
            for idx, row in df.iterrows():
                if pd.isna(row["meta_desc"]):
                    temp.append(row["url"])
            DESCRIPTION_EMPTY = set(temp)
            if not DESCRIPTION_EMPTY:
                return "Harika meta description'a sahip olmayan bir adres ile karşılaşılmadı :) "
            else: 
                return DESCRIPTION_EMPTY
        else:
            descInfo = "Descripton hakkında bilgi alınamadı. Description kullanılmamış"
            return descInfo
    except Exception as e:
        return str(e) 

 #title tag ının olup olmadığını kontrol eder      
def titleEmpty(TITLE_EMPTY,titleInfo,df,temp):
    try:
        if "title" in df.columns:
            for idx, row in df.iterrows():
                if pd.isna(row["title"]):
                    temp.append(row["url"])
            TITLE_EMPTY = set(temp)
            if not TITLE_EMPTY:
                return "Harika title etiketine sahip olmayan bir sayfa bulunmadı :)"
            else: 
                return TITLE_EMPTY
        else:
            titleInfo = "Title etiketi hakkında bilg alınamadı. /Title etiketi kullanılmamış"
            return titleInfo
    except Exception as e:
        return str(e) 



def longDesc(DESCRIPTION_LONG,descInfo,df,temp):  #description' ın uzunluğunu test eder
    try:
        if "meta_desc" in df.columns:
            for idx, row in df.iterrows():
                boyut = str(row["meta_desc"])
                if len(boyut)>160:
                    temp.append(row["url"])
            DESCRIPTION_LONG = set(temp)
            if not DESCRIPTION_LONG:
                return "Harika tüm adreslerde meta açıklamaların uzun bulunmadı :) "
            return DESCRIPTION_LONG
        else:
            descInfo = "Descripton hakkında bilgi alınamadı. Description kullanılmamış"
            return descInfo
    except Exception as e:
        return str(e) 



def shortDesc(DESCRIPTION_SHORT,descInfo,df,temp):  #description' ın uzunluğunu test eder
    try:
        if "meta_desc" in df.columns:
            for idx, row in df.iterrows():
                boyut = str(row["meta_desc"])
                if len(boyut)<50:
                    temp.append(row["url"])
            DESCRIPTION_SHORT = set(temp)
            if not DESCRIPTION_SHORT: 
                return "Harika tüm adreslerde meta açıklamanın uzunluğu kısa değil :)"
            else:
                return DESCRIPTION_SHORT
        else:
            descInfo = "Descripton hakkında bilgi alınamadı. Description kullanılmamış"
            return descInfo
    except Exception as e:
        return str(e) 


#canonic url kullanılmayan adresleri tespit eder
def canonicalMissing(CANONICAL_NOT,canonicInfo,df,temp):
    try:
        if "canonical" in df.columns:
            for idx, row in df.iterrows():
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
    except Exception as e:
        return str(e) 

 #img alt tagında açıklaması eksik olan adresleri verir
def imgAltNot(IMG_ALT_NOT,imgInfo,df, temp):
    try:
        if "img_src" in df.columns:
            for idx, row in df.iterrows():
                if pd.notna(row["img_src"]):
                    img_alt_value = row["img_alt"]
                    if pd.isna(img_alt_value):
                        temp.append(row["url"])
            IMG_ALT_NOT = set(temp)
            if not IMG_ALT_NOT:
                return "Harika IMG açıklmalarına tüm adreslerde yer verilmiş :)"
            return set(IMG_ALT_NOT)
        else:
            imgInfo = "Img alt etiketi hakkında bilgi alınamadı. Img kullanılmamış"
            return imgInfo
    except Exception as e:
        return str(e) 


def imgAltEmpty(IMG_ALT_EMPTY,imgInfo,df,temp):
    try:
        if "img_src" in df.columns:
            for idx, row in df.iterrows():
                if pd.notna(row["img_src"]):
                    img_alt = str(row["img_alt"])
                    if "@@@" in img_alt:
                        temp.append(row["url"])
            IMG_ALT_EMPTY = set(temp)
            if not IMG_ALT_EMPTY:
                return "Harika img açıklamaları tüm adreslerde dolu görünüyor :)"
            return IMG_ALT_EMPTY
        else:
            imgInfo = "Img alt etiketi hakkında bilgi alınamadı. Img kullanılmamış"
            return imgInfo    
    except Exception as e:
        return str(e) 

# fonksiyonlar nan yada değer döndürürp boş olabilir bunu göz önünde bulunurup kodu ona göre yazman lazım. 
#nan ise mesela zaten ölçmeye gerek yok 
#@@@ ise ancak o zaman urlleri doldurur



def disallowRobots(ROBOTS_TXT_DISALLOW,robotsIsNot,temp):
    try:
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
    except Exception as e:
        return str(e) 
    
def redirectImage(REDIRECT_IMG_URL,imgInfo,df,temp):
    try:
        if "img_src" in df.columns:
            for idx, row in df.iterrows():
                if pd.notna(row["img_src"]):
                    img_srcc = str(row["img_src"])
                    if "http" in img_srcc:
                        temp.append(row["url"])
            REDIRECT_IMG_URL = set(temp)
            if not REDIRECT_IMG_URL:
                return "Harika img etiketlerinde bir web adresinden kaynak bulunmadı :)"
            return REDIRECT_IMG_URL
        else:
            imgInfo = "Img alt etiketi hakkında bilgi alınamadı. Img kullanılmamış"
            return imgInfo  
    except Exception as e:
        return str(e) 


def serverErrors(STATUS_CODE_5XX, df,temp):
    try:
        for idx, row in df.iterrows():
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
    except Exception as e:
        return str(e)    
    
def movedPermanently(STATUS_CODE_301,df, temp):
    try:
        for idx, row in df.iterrows():
            if pd.notna(row["status"]):
                status301 = str(row["status"])
                if status301 == "301": #durum kodunun 301 olduğunu test etmek için yazılmıştır.
                    temp.append(row["url"])
            else:
                return "Durum kodu bilgisine ulaşılamadı. Daha sonra tekrar deneyiniz."
        STATUS_CODE_301 = set(temp)
        if not STATUS_CODE_301:
            return "Sayfalarda 301 kaynak kalıcı olarak taşındı durum koduna rastlanmadı :)"
        else:
            return STATUS_CODE_301
    except Exception as e:
        return str(e) 
    
def movedTemporarily(STATUs_CODE_302,df, temp):
    try:
        for idx, row in df.iterrows():
            if pd.notna(row["status"]):
                status302 = str(row["status"])
                if status302 == "302": #durum kodunun 302 olduğunu test etmek için yazılmıştır.
                    temp.append(row["url"])
            else:
                return "Durum kodu bilgisine ulaşılamadı. Daha sonra tekrar deneyiniz."
        STATUS_CODE_302 = set(temp)
        if not STATUS_CODE_302:
            return "Sayfalarda 302 kaynak geçici olarak taşındı durum koduna rastlanmadı :)"
        else:
            return STATUS_CODE_302
    except Exception as e:
        return str(e) 



def formatTime(seconds): #tarama süresini saat.dakika.saniye formatına dönüştürür
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return int(hours), int(minutes), seconds



@app.route('/web', methods=['POST', 'GET'])
@app.route('/web/crawl', methods=['POST', 'GET'])
def webCrawlerFromForm():
    if request.method == "POST":
        url = request.form.get('url')
        jl_file_name = f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}_output.jl"
        if not url:
            return "URL girilmedi"
        startTime = None
        x, y, df,startTime = isValidUrl(url,jl_file_name)
        if y:
            test_sonuc = "TEST SONUÇLARI" #webCrawler.html için oluşturulan eğer sayfa taranmmışsa dönen değişken
            if df is not None and not df.empty:
                IMG_ALT_EMPTY = []
                IMG_ALT_NOT = []
                ROBOTS_TXT_DISALLOW = []
                temp =[] 
                canonicInfo = None
                h1Info =""
                descInfo = ""
                imgInfo = ""
                titleInfo = ""
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
                endTime = time.time()
                crawlingTime = endTime - startTime
                hours, minutes, seconds = formatTime(crawlingTime) # tarama süresini saat dakika saniye olarak verir
                #clear_lists()
                print(df.columns)
                # HTML şablonuna sonuçları gönder Fonksiyon kontrolü için uygulanablir.
                #htmlOut = df.to_html(f"{url.replace('http://', '').replace('https://', '').replace('/', '').replace('.com', '')}.html")
                deleteFile(jl_file_name)
                
                
                return render_template('webCrawl.html', test_sonuc1=test_sonuc, h1isnot=h1Avaliable(H1_NOT,h1Info, df,temp=[]),badstatus=badStatus(STATUS_CODE_BAD, df,temp=[]), status4xx=clientError(STATUS_CODE_4xx,df, temp=[]),
                                        h1duplicate=duplicateH1(H1_DUPLICATE,h1Info,df, temp=[]),
                                    time=pageOpeningTime(load_times,df, temp=[]),emptyDescription=descriptionMissing(DESCRIPTION_EMPTY,descInfo,df,temp=[]), 
                                    notTitle=titleEmpty(TITLE_EMPTY,titleInfo, df,temp=[]), descLong = longDesc(DESCRIPTION_LONG,descInfo,df,temp=[]), descShort =shortDesc(DESCRIPTION_SHORT,descInfo,df,temp=[]),
                                    notcanonic=canonicalMissing(CANONICAL_NOT,canonicInfo,df,temp=[]),imgAltNot=imgAltNot(IMG_ALT_NOT,imgInfo,df, temp=[]), 
                                    imgAltEmpty=imgAltEmpty(IMG_ALT_EMPTY,imgInfo,df,temp=[]),robots =disallowRobots(ROBOTS_TXT_DISALLOW,robotsIsNot,temp=[]), redirectImg=redirectImage(REDIRECT_IMG_URL,imgInfo,df,temp)
                                    ,status5xx = serverErrors(STATUS_CODE_5XX,df,temp=[]), status301=movedPermanently(STATUS_CODE_301,df, temp=[]), status302 = movedTemporarily(STATUS_CODE_302,df,temp=[]),
                                        crawltime=f"{hours:02d}h {minutes:02d}m {seconds:.0f}s")

        if not y:
            if df is not None and "errors" in df.columns  : #oluşturulan işlevsiz df silinecektir
                deleteFile(jl_file_name) 
            return render_template("web.html" ,labelIndex=x)
            
    else:
        test_sonuc= "Upps Sanırım Tarama Henüz Yapılmamış"
        return render_template('web.html', test_sonuc2=test_sonuc)
    

    

@app.errorhandler(404) #404 durum kodlarının yakalanması 
def not_found(e):
  if '/404' in request.path: #404 sayfası aranıyorsa render et
    return render_template('404.html'), 404
  else:
      return redirect(url_for('error_404')) #eğer uzantı 404 değilse error_404 fonksiyonu ile render eder

@app.route('/404') #redirect 404 addr
def error_404():
    return render_template('404.html'), 404

if __name__ == '__main__':
   
    serve(app, host='0.0.0.0', port=5000)
    app.debug=False
   

