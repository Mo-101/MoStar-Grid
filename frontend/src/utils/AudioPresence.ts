export class AudioPresence {
  private ctx: AudioContext | null = null;
  private humOsc: OscillatorNode | null = null;
  private humGain: GainNode | null = null;
  private isAwake: boolean = false;

  private initContext() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public wakeGrid() {
    if (this.isAwake) return;
    this.initContext();
    if (!this.ctx) return;

    // Ambient hum (low blue resonance tone)
    this.humOsc = this.ctx.createOscillator();
    this.humOsc.type = "sine";
    this.humOsc.frequency.setValueAtTime(55, this.ctx.currentTime); // Deep A tone

    this.humGain = this.ctx.createGain();
    this.humGain.gain.setValueAtTime(0, this.ctx.currentTime);
    this.humGain.gain.linearRampToValueAtTime(0.08, this.ctx.currentTime + 3); // Slow fade in

    this.humOsc.connect(this.humGain);
    this.humGain.connect(this.ctx.destination);
    
    this.humOsc.start();
    this.isAwake = true;
  }

  public dipHumForVoice() {
    if (!this.ctx || !this.humGain) return;
    this.humGain.gain.linearRampToValueAtTime(0.02, this.ctx.currentTime + 0.5);
  }

  public restoreHum() {
    if (!this.ctx || !this.humGain) return;
    this.humGain.gain.linearRampToValueAtTime(0.08, this.ctx.currentTime + 1.5);
  }

  public playChime(severity: string = "high") {
    this.initContext();
    if (!this.ctx) return;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.connect(gain);
    gain.connect(this.ctx.destination);

    const now = this.ctx.currentTime;
    
    // Frequency based on severity
    let freq1 = 440;
    let freq2 = 880;
    if (severity === "critical") {
      freq1 = 880;
      freq2 = 1760;
      osc.type = "triangle";
    } else {
      osc.type = "sine";
    }

    osc.frequency.setValueAtTime(freq1, now);
    osc.frequency.exponentialRampToValueAtTime(freq2, now + 0.1);

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.3, now + 0.05);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 1.5);

    osc.start(now);
    osc.stop(now + 1.6);
  }

  public stop() {
    if (this.humOsc) {
      this.humOsc.stop();
      this.humOsc.disconnect();
      this.humOsc = null;
    }
    if (this.humGain) {
      this.humGain.disconnect();
      this.humGain = null;
    }
    this.isAwake = false;
  }
}

export const audioPresence = new AudioPresence();
