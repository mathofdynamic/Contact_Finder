FROM python:3.10-alpine

# 1) install chromium & chromedriver + system deps for headless rendering
RUN apk add --no-cache \
      chromium \
      chromium-chromedriver \
      nss \
      freetype \
      harfbuzz \
      ttf-freefont

# 2) point Selenium at the Alpine chromium
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) install Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) copy app code
COPY . .

# 5) expose & run
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "Contact_extractor:app"]
