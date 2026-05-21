# =========================
# USE PYTHON IMAGE
# =========================

FROM python:3.11-slim

# =========================
# SET WORK DIRECTORY
# =========================

WORKDIR /app

# =========================
# COPY FILES
# =========================

COPY . .

# =========================
# INSTALL REQUIREMENTS
# =========================

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# EXPOSE PORT
# =========================

EXPOSE 5000

# =========================
# RUN APP
# =========================

CMD ["python", "app.py"]