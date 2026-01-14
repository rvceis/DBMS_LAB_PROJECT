
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ----------------- 4. Roller Coaster Track -----------------
t = np.linspace(0, 4*np.pi, 500)  # time parameter
R = 3                              # radius of spiral
x_track = R * np.cos(t)
y_track = R * np.sin(t)
z_track = np.sin(2*t) + t/2        # adds loops and rising slope

fig = plt.figure(figsize=(8,5))
ax = fig.add_subplot(111, projection='3d')
ax.plot(x_track, y_track, z_track, color='red', lw=2)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Roller Coaster Track')
plt.savefig("roller_coaster.png")
plt.show()

# ----------------- 5. Antenna Array -----------------
N = 20              # grid size
H = 5               # maximum height
R_grid = N / 2      # radius to decrease height
i_c, j_c = N/2, N/2 # center of grid

i = np.arange(0, N+1)
j = np.arange(0, N+1)
I, J = np.meshgrid(i, j)

# height function: tallest at center, decreases outward
h = H * (1 - ((I-i_c)**2 + (J-j_c)**2)/R_grid**2)
h[h < 0] = 0  # no negative heights

fig2 = plt.figure(figsize=(8,5))
ax2 = fig2.add_subplot(111, projection='3d')
ax2.bar3d(I.flatten(), J.flatten(), np.zeros_like(h.flatten()), 0.5, 0.5, h.flatten(), shade=True, color='green')
ax2.set_xlabel('i')
ax2.set_ylabel('j')
ax2.set_zlabel('Height h(i,j)')
ax2.set_title('Antenna Array on Rooftop')
plt.savefig("antenna_array.png")
plt.show()
