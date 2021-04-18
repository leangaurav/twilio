FROM continuumio/miniconda3

WORKDIR /app

# install requirements
COPY TwilioVoiceEcho/requirements.txt .
RUN pip install -r requirements.txt

COPY py_modules ./modules

COPY TwilioVoiceEcho ./

ENV PYTHONPATH=".:/app/modules"
ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["python"]
