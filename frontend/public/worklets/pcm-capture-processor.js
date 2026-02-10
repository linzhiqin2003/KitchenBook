/**
 * AudioWorklet processor: captures 16 kHz Int16 PCM chunks and computes RMS energy.
 *
 * Expected AudioContext sampleRate = 16000.
 * Posts messages: { type: 'pcm', buffer: Int16Array, rms: number }
 */
class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super()
    // Default chunk = 8000 samples = 0.5 s at 16 kHz
    this.chunkSize = options?.processorOptions?.chunkSize || 8000
    this.buffer = new Float32Array(this.chunkSize)
    this.offset = 0
  }

  process(inputs) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const channelData = input[0] // mono
    let i = 0

    while (i < channelData.length) {
      const remaining = this.chunkSize - this.offset
      const toCopy = Math.min(remaining, channelData.length - i)
      this.buffer.set(channelData.subarray(i, i + toCopy), this.offset)
      this.offset += toCopy
      i += toCopy

      if (this.offset >= this.chunkSize) {
        this._flush()
      }
    }

    return true
  }

  _flush() {
    // Compute RMS
    let sumSq = 0
    for (let j = 0; j < this.offset; j++) {
      sumSq += this.buffer[j] * this.buffer[j]
    }
    const rms = Math.sqrt(sumSq / this.offset)

    // Float32 → Int16
    const int16 = new Int16Array(this.offset)
    for (let j = 0; j < this.offset; j++) {
      const s = Math.max(-1, Math.min(1, this.buffer[j]))
      int16[j] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }

    this.port.postMessage({ type: 'pcm', buffer: int16.buffer, rms }, [int16.buffer])

    // Reset
    this.buffer = new Float32Array(this.chunkSize)
    this.offset = 0
  }
}

registerProcessor('pcm-capture-processor', PcmCaptureProcessor)
