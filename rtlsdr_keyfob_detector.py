#!/usr/bin/env python3
"""
RTL-SDR keyfob detector using pyrtlsdr + numpy (no GNU Radio required).

- Center frequency: 315 MHz (set CENTER_FREQ to change).
- Does a short calibration to estimate noise floor, then monitors continuously.
- Prints timestamp + envelope value when detection happens.

Dependencies:
  sudo apt install rtl-sdr
  pip3 install pyrtlsdr numpy

Run:
  python3 rtl_sdr_keyfob_detector.py
"""

import time
from datetime import datetime
import numpy as np
from rtlsdr import RtlSdr

# -------------------- USER PARAMETERS --------------------
CENTER_FREQ = 315e6        # Hz (315 MHz)
SAMPLE_RATE = 1.024e6      # Hz (1.024 MS/s is commonly supported)
GAIN = 'auto'              # or a number like 30
BLOCK_DURATION = 0.2       # seconds per read block (0.1-0.5 is fine)
SUBBLOCK_MS = 5            # milliseconds per envelope sample (e.g., 5 ms)
CALIBRATION_SECONDS = 3.0  # collect this many seconds for noise-floor estimate
THRESHOLD_FACTOR = 8.0     # detection threshold = noise_median * THRESHOLD_FACTOR
HYSTERESIS_FACTOR = 0.6    # fraction to drop threshold for clearing
DEBOUNCE_MS = 200          # minimum ms between printed triggers
# ---------------------------------------------------------

def collect_block(sdr, n_samples):
    """Read exactly n_samples from SDR and return complex64 numpy array."""
    return sdr.read_samples(n_samples)

def block_envelope_means(iq_samples, sample_rate, subblock_ms=5):
    """
    Convert IQ block -> array of mean power values for each subblock of subblock_ms length.
    Returns 1-D float32 numpy array of mean(power) per subblock.
    """
    power = np.abs(iq_samples)**2  # instantaneous power
    subblock_len = max(1, int(sample_rate * (subblock_ms / 1000.0)))
    # trim samples to integer multiple of subblock_len
    n = (len(power) // subblock_len) * subblock_len
    if n == 0:
        return np.array([], dtype=np.float32)
    power = power[:n]
    # reshape and compute mean per subblock
    power_matrix = power.reshape(-1, subblock_len)
    means = power_matrix.mean(axis=1).astype(np.float32)
    return means

def calibrate_noise(sdr, sample_rate, block_duration, calibration_seconds, subblock_ms):
    """
    Read for calibration_seconds and return a robust noise estimate (median of subblock means).
    """
    print(f"[i] Calibrating noise floor for {calibration_seconds:.1f} seconds... (keep keyfob quiet)")
    dims_per_block = int(block_duration * sample_rate)
    blocks_needed = max(1, int(np.ceil(calibration_seconds / block_duration)))
    all_means = []
    for i in range(blocks_needed):
        samples = collect_block(sdr, dims_per_block)
        means = block_envelope_means(samples, sample_rate, subblock_ms=subblock_ms)
        if means.size:
            all_means.append(means)
    if not all_means:
        raise RuntimeError("Calibration failed: no samples read.")
    all_means = np.concatenate(all_means)
    noise_median = float(np.median(all_means))
    noise_mean = float(np.mean(all_means))
    noise_std = float(np.std(all_means))
    print(f"[i] Calibration done: median={noise_median:.4e}, mean={noise_mean:.4e}, std={noise_std:.4e}")
    return noise_median, noise_mean, noise_std

def main():
    # Derived params
    block_n_samples = int(BLOCK_DURATION * SAMPLE_RATE)
    subblock_ms = SUBBLOCK_MS
    debounce_s = DEBOUNCE_MS / 1000.0

    print("[*] Opening RTL-SDR device...")
    sdr = RtlSdr()
    sdr.sample_rate = SAMPLE_RATE
    sdr.center_freq = CENTER_FREQ
    if GAIN == 'auto':
        try:
            sdr.gain = 'auto'
        except Exception:
            # some pyrtlsdr versions expect numeric gain; ignore
            pass
    else:
        sdr.gain = GAIN

    try:
        # Calibration
        noise_median, noise_mean, noise_std = calibrate_noise(
            sdr, SAMPLE_RATE, BLOCK_DURATION, CALIBRATION_SECONDS, subblock_ms
        )
        threshold_on = noise_median * THRESHOLD_FACTOR
        threshold_off = threshold_on * (1.0 - HYSTERESIS_FACTOR)
        print(f"[i] Detection thresholds: on={threshold_on:.4e}, off={threshold_off:.4e}")
        print(f"[*] Monitoring {CENTER_FREQ/1e6:.3f} MHz   sample_rate={SAMPLE_RATE/1e6:.3f} MS/s")
        last_trigger = 0.0
        triggered = False

        while True:
            samples = collect_block(sdr, block_n_samples)
            means = block_envelope_means(samples, SAMPLE_RATE, subblock_ms=subblock_ms)
            if means.size == 0:
                time.sleep(0.01)
                continue

            # find the maximum mean in this block (peak envelope)
            peak = float(np.max(means))
            avg = float(np.mean(means))

            now = time.time()
            # detection logic with hysteresis
            if (not triggered and peak >= threshold_on and (now - last_trigger) >= debounce_s):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print(f"[{ts}] Detected! peak={peak:.4e}  avg={avg:.4e}")
                triggered = True
                last_trigger = now

            elif triggered and peak < threshold_off:
                # cleared
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print(f"[{ts}] Cleared. peak={peak:.4e}  avg={avg:.4e}")
                triggered = False

            # small sleep (loop pacing)
            # no sleep needed because reading blocks is paced by RTL sampling, but include tiny pause
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting.")
    finally:
        sdr.close()

if __name__ == "__main__":
    main()
