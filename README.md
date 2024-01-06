# 🌐  [SEO Crawler](https://github.com/BilgeNurBekar/seo-project-1)

SEO crawler projesi, sayfa içi SEO hakkında dosya ve url tabanlı inceleme imkanı sunan ve geliştirilmeye devam eden bir projedir.

## 💻 Installations

- Python 3.x
- advertools==0.13.5
- Flask==3.0.0
- pandas==2.1.4
- waitress==2.1.2.


Projenin yerel ortamınızda çalıştırılması için aşağıdaki adımları takip edebilirsiniz:

1. Git deposunu klonlayın:

    ```bash
    git clone https://github.com/BilgeNurBekar/seo-project-1.git
    ```

2. Proje dizinine gidin:

     ```bash
    cd seo-project-1-main/
    ```

3. Sanal ortamı oluşturun:

    ```bash
    python -m venv ./venv
    ```

4. Sanal ortamı etkinleştirin:

    - Windows için:

        ```bash
        .\venv\Scripts\activate
        ```

    - Unix veya MacOS için:

        ```bash
        source venv/bin/activate
        ```

5. Gerekli bağımlılıkları yükleyin:

    ```bash
    pip install -r requirements.txt
    ```

6. Uygulamayı çalıştırın:

    ```bash
    web: waitress-serve --host=127.0.0.1 --port=5000 main:app 
    ```
 
