from google.cloud import speech_v1 as speech
from google.cloud.speech_v1.types import StreamingRecognitionConfig
import dataclasses

from enum import Enum

class AsrType(Enum):
    GOOGLE = 1

class AudioEncoding(Enum):
    MULAW = 1
    LINEAR16 = 2


@dataclasses.dataclass
class AsrConfig:
    encoding: AudioEncoding
    sample_rate: int
    language: str
    asr_type: AsrType # google/assembly etc.

    def to_client_config(self):
        if self.asr_type == AsrType.GOOGLE:
            return self._to_google_config()

        raise ValueError("unsupported asr type")

    def _to_google_config(self):
        config = speech.RecognitionConfig()
        if self.encoding == AudioEncoding.MULAW:
            config.encoding = speech.RecognitionConfig.AudioEncoding.MULAW
        elif self.encoding == AudioEncoding.LINEAR16:
            config.encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        else:
            raise ValueError("unsupported encoding")

        # todo: add validation
        config.sample_rate_hertz = self.sample_rate

        # todo: add validation
        config.language_code = self.language
        return StreamingRecognitionConfig(config=config)

async def get_async_streaming_asr_client(asr_config: AsrConfig, audio_iterator):
    async_google_client = speech.SpeechAsyncClient()

    async def request_generator(config: AsrConfig):
        # return audio config
        yield speech.StreamingRecognizeRequest(streaming_config=config.to_client_config())

        # return audio chunks
        async for audio in audio_iterator:
            print("three")
            yield speech.StreamingRecognizeRequest(audio_content=audio)

    # Make the request
    try:
        stream = await async_google_client.streaming_recognize(requests=request_generator(asr_config))
    except Exception as err:
        print("crashed", err)
        raise
    print("get asr done")
    return stream
