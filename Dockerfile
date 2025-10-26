FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# fail build if welcome.py isn't in the image
RUN ls -al && test -f welcome.py
SHELL ["/bin/sh","-c"]
CMD exec python -m streamlit run welcome.py --server.address 0.0.0.0 --server.port ${PORT:-8080}