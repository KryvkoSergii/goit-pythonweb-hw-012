FROM python:3.13-slim
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY . .
RUN pip install poetry
RUN poetry install
EXPOSE 8000
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]