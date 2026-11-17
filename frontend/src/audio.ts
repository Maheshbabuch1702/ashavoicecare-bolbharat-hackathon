/**
 * Microphone capture and TTS playback.
 *
 * AudioWorklet emits 512-sample chunks -> exactly 1024 bytes as 16-bit PCM,
 * which is the frame size Gnani's streaming STT requires. The browser's native
 * sample rate is declared to the backend instead of resampling, because Gnani
 * accepts 8 / 16 / 44.1 / 48 kHz sources directly.
 */

const WORKLET_SOURCE = `
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(512);
    this.filled = 0;
  }
  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (!channel) return true;
    for (let i = 0; i < channel.length; i++) {
      this.buffer[this.filled++] = channel[i];
      if (this.filled === this.buffer.length) {
        this.port.postMessage(this.buffer.slice(0));
        this.filled = 0;
      }
    }
    return true;
  }
}
registerProcessor("pcm-processor", PCMProcessor);
`;

const SUPPORTED_RATES = [8000, 16000, 44100, 48000];

export interface VoiceClientOptions {
  onFrame: (frame: ArrayBuffer) => void;
  onLevel?: (level: number) => void;
  onBargeIn?: () => void;
}

export class VoiceClient {
  private context: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private node: AudioWorkletNode | null = null;
  private sink: GainNode | null = null;
  private source: AudioBufferSourceNode | null = null;
  private workletReady = false;
  private bargeFrames = 0;

  muted = false;
  playing = false;
  onFrame: (frame: ArrayBuffer) => void;
  onLevel?: (level: number) => void;
  onBargeIn?: () => void;

  constructor(options: VoiceClientOptions) {
    this.onFrame = options.onFrame;
    this.onLevel = options.onLevel;
    this.onBargeIn = options.onBargeIn;
  }

  get sampleRate(): number {
    return this.context?.sampleRate ?? 16000;
  }

  get active(): boolean {
    return this.stream !== null;
  }

  async start(): Promise<void> {
    if (!this.context) this.context = await this.createContext();
    if (this.context.state === "suspended") await this.context.resume();

    if (!this.workletReady) {
      const blob = new Blob([WORKLET_SOURCE], { type: "application/javascript" });
      const url = URL.createObjectURL(blob);
      try {
        await this.context.audioWorklet.addModule(url);
        this.workletReady = true;
      } finally {
        URL.revokeObjectURL(url);
      }
    }

    if (!this.stream) {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    }
    if (this.node) return;

    const input = this.context.createMediaStreamSource(this.stream);
    this.node = new AudioWorkletNode(this.context, "pcm-processor");
    // A zero-gain sink keeps the graph pulling audio without echoing the mic.
    this.sink = this.context.createGain();
    this.sink.gain.value = 0;
    input.connect(this.node);
    this.node.connect(this.sink);
    this.sink.connect(this.context.destination);

    this.node.port.onmessage = (event: MessageEvent<Float32Array>) => this.handleChunk(event.data);
  }

  private async createContext(): Promise<AudioContext> {
    // Request 16 kHz first; fall back to the device default if unsupported.
    for (const rate of [16000, 48000]) {
      try {
        const context = new AudioContext({ sampleRate: rate, latencyHint: "interactive" });
        if (SUPPORTED_RATES.includes(context.sampleRate)) return context;
        await context.close();
      } catch {
        // try the next rate
      }
    }
    return new AudioContext({ latencyHint: "interactive" });
  }

  private handleChunk(samples: Float32Array): void {
    let energy = 0;
    for (let i = 0; i < samples.length; i++) energy += samples[i] * samples[i];
    const rms = Math.sqrt(energy / samples.length);
    this.onLevel?.(Math.min(1, rms * 6));

    if (this.playing && !this.muted) {
      // Local barge-in: stop the assistant the moment the worker speaks.
      if (rms > 0.035) {
        this.bargeFrames += 1;
        if (this.bargeFrames >= 3) {
          this.bargeFrames = 0;
          this.onBargeIn?.();
        }
      } else {
        this.bargeFrames = 0;
      }
    }

    if (this.muted) return;

    const pcm = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      const value = Math.max(-1, Math.min(1, samples[i]));
      pcm[i] = value < 0 ? value * 0x8000 : value * 0x7fff;
    }
    this.onFrame(pcm.buffer);
  }

  async play(wav: ArrayBuffer, options: { mute?: boolean } = {}): Promise<void> {
    if (!this.context) return;
    this.stop();
    const buffer = await this.context.decodeAudioData(wav.slice(0));
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.context.destination);
    this.source = source;
    this.playing = true;
    const previousMute = this.muted;
    this.muted = options.mute ?? false;
    this.bargeFrames = 0;
    await new Promise<void>((resolve) => {
      source.onended = () => {
        this.playing = false;
        this.source = null;
        this.muted = previousMute;
        resolve();
      };
      source.start();
    });
  }

  stop(): void {
    if (this.source) {
      try {
        this.source.onended = null;
        this.source.stop();
      } catch {
        // already stopped
      }
      this.source = null;
    }
    this.playing = false;
    this.muted = false;
  }

  /** Release the microphone but keep the audio context alive for playback. */
  micOff(): void {
    this.node?.disconnect();
    this.sink?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.node = null;
    this.sink = null;
  }

  async dispose(): Promise<void> {
    this.stop();
    this.micOff();
    if (this.context) {
      await this.context.close().catch(() => undefined);
      this.context = null;
      this.workletReady = false;
    }
  }
}
