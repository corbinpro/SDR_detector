import numpy as np

# --- USER SETTINGS ---
filename = "fob_output.bin"  # your File Sink output
fs = 500_000  # sample rate after decimation (Hz)

# --- LOAD DATA ---
bits = np.fromfile(filename, dtype=np.uint8)

# --- FIND PULSE EDGES ---
# rising edges: 0 → 1
# falling edges: 1 → 0
edges = np.diff(bits)
rising_idx = np.where(edges == 1)[0] + 1
falling_idx = np.where(edges == -1)[0] + 1

# --- HANDLE FILE START/END ---
if bits[0] == 1:
    rising_idx = np.insert(rising_idx, 0, 0)
if bits[-1] == 1:
    falling_idx = np.append(falling_idx, len(bits))

# --- CALCULATE PULSE DURATIONS ---
pulse_durations = (falling_idx - rising_idx) / fs  # in seconds
pulse_values = bits[rising_idx]  # should all be 1

# --- PRINT RESULTS ---
print("Detected pulses:")
for i, (start, end, dur) in enumerate(zip(rising_idx, falling_idx, pulse_durations)):
    print(
        f"Pulse {i + 1}: start={start / fs:.6f}s, end={end / fs:.6f}s, duration={dur * 1e3:.2f} ms"
    )

# --- OPTIONAL: RECONSTRUCT BIT SEQUENCE ---
# If your key fob uses fixed-width OOK pulses, you can map duration → '0' or '1'
# Example thresholds (adjust according to your measured pulses):
threshold_ms = 0.5  # pulse longer than this = '1', shorter = '0'
bit_sequence = ["1" if dur * 1e3 > threshold_ms else "0" for dur in pulse_durations]

print("\nApproximate bit sequence:")
print("".join(bit_sequence))
