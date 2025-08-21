# Ganti dengan versi Python yang sesuai
FROM python:3.12.7

# RUN which python
# RUN git clone https://github.com/johnrobert7991/WaBotPython.git /waBotPython
# Membuat direktori kerja
RUN mkdir -p /chat_nakes

# Set direktori kerja
WORKDIR /chat_nakes

# Menyalin semua file dari direktori saat ini ke dalam image
COPY . .

# Instal dependensi dari requirements.txts
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update -y && apt install ffmpeg -y
RUN curl -fsSL https://nodejs.org/dist/v20.18.1/node-v20.18.1-linux-x64.tar.xz \
      | tar -xJ -C /usr/local --strip-components=1

# Menginformasikan Docker bahwa aplikasi mendengarkan pada port 80
EXPOSE 3000

RUN chmod +x entrypoint.sh
# CMD ["ls"]
# CMD ["gunicorn", "--bind" , ":3000", "--workers", "2", "app:main"]
# CMD ["python3", "app.py"]
CMD ["./entrypoint.sh"]
