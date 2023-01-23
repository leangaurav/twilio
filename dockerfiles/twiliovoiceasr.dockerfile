FROM continuumio/miniconda3

WORKDIR /app

# install requirements
COPY TwilioVoiceToAsr/requirements.txt .
RUN pip install -r requirements.txt

COPY TwilioVoiceToAsr ./

ENV PYTHONPATH="."
ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["python"]
