FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY src ./src
COPY pages ./pages
COPY assets ./assets
COPY .streamlit ./.streamlit
COPY data/catalog.csv data/manifest.json data/README.md ./data/
RUN useradd --create-home lab && mkdir -p /var/lib/songmatch && chown -R lab:lab /app /var/lib/songmatch
USER lab
ENV SONGMATCH_DB_PATH=/var/lib/songmatch/feedback.db
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"
CMD ["python","-m","streamlit","run","app.py","--global.developmentMode=false","--server.address=0.0.0.0","--server.port=8501"]
