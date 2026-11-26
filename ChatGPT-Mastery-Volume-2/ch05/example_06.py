"""
Production Digital Signal Processing (DSP) Audio Resampler
Converts arbitrary multi-channel audio to single-channel 24kHz PCM16 or 8kHz G.711.
Author: Vatsal Shah, Enterprise AI Architect
"""
import numpy as np
from scipy import signal

class EnterpriseAudioDSP:
    @staticmethod
    def resample_to_pcm16_24k(raw_audio_float: np.ndarray, orig_sample_rate: int) -> bytes:
        """
        Resamples floating point audio [-1.0, 1.0] to 24kHz 16-bit linear PCM.
        Applies polyphase anti-aliasing filtering.
        """
        # 1. Downmix to single-channel mono if stereo
        if raw_audio_float.ndim > 1:
            raw_audio_float = np.mean(raw_audio_float, axis=1)

        # 2. Resample using Polyphase Sinc Filtering
        target_rate = 24000
        if orig_sample_rate != target_rate:
            gcd = np.gcd(orig_sample_rate, target_rate)
            up = target_rate // gcd
            down = orig_sample_rate // gcd
            resampled = signal.resample_poly(raw_audio_float, up, down)
        else:
            resampled = raw_audio_float

        # 3. Clip and Quantize to 16-bit Signed Integers (-32768 to 32767)
        resampled_clipped = np.clip(resampled, -1.0, 1.0)
        pcm16_integers = (resampled_clipped * 32767.0).astype(np.int16)
        
        # 4. Pack into Little-Endian Raw Bytes
        return pcm16_integers.tobytes()

    @staticmethod
    def linear_pcm_to_mulaw(pcm16_bytes: bytes) -> bytes:
        """
        Mathematically converts 16-bit linear PCM samples to 8-bit G.711 μ-law bytes.
        """
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32)
        # Normalize to [-1.0, 1.0]
        norm = samples / 32768.0
        
        # μ-law transformation: sgn(x) * ln(1 + 255|x|) / ln(256)
        mu = 255.0
        sgn = np.sign(norm)
        magnitude = np.abs(norm)
        companded = sgn * (np.log(1.0 + mu * magnitude) / np.log(1.0 + mu))
        
        # Quantize to 8-bit unsigned integer (0 to 255)
        quantized = ((companded + 1.0) / 2.0 * 255.0).astype(np.uint8)
        return quantized.tobytes()
