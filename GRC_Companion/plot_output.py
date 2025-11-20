import numpy as np
import matplotlib.pyplot as plt

fs = 500000  # sample rate after decimation
bits = np.fromfile("fob_output.bin", dtype=np.uint8)

plt.figure()
plt.step(np.arange(len(bits)) / fs, bits, where="post")
plt.xlabel("Time [s]")
plt.ylabel("Binary Level")
plt.title("Thresholded Keyfob Bits")
plt.show()
