import numpy as np
import matplotlib.pyplot as plt


plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

x = np.linspace(-2 * np.pi, 2 * np.pi, 800)
fig, ax = plt.subplots(figsize=(8.2, 5.5), dpi=130)

ax.plot(x, np.sin(x), color="#2f83a8", linewidth=2.4, label="正弦曲线")
ax.plot(x, np.cos(x), color="#f28e2b", linewidth=2.4, label="余弦曲线")
ax.set(xlim=(-2 * np.pi, 2 * np.pi), ylim=(-1.1, 1.1), facecolor="white")

for name in ["left", "bottom"]:
    ax.spines[name].set_position("zero")
    ax.spines[name].set(color="#444444", linewidth=1.6)
for name in ["right", "top"]:
    ax.spines[name].set_visible(False)

pi_ticks = np.array([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2]) * np.pi
pi_labels = [r"$-2\pi$", r"$-3\pi/2$", r"$-\pi$", r"$-\pi/2$", "0",
             r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"]
ax.set_xticks(pi_ticks, pi_labels, fontsize=12)
ax.set_yticks([-1, -0.5, 0, 0.5, 1], ["-1.0", "-0.5", "0.0", "0.5", "1.0"], fontsize=12)
ax.tick_params(axis="both", direction="out", length=4, width=1, colors="#222222", pad=8)

ax.legend(loc="upper right", framealpha=0.92, facecolor="white", edgecolor="#dddddd", fontsize=13)
plt.tight_layout()
plt.show()