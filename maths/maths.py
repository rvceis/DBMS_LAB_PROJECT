import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 1. Drone Path (spiral around cylinder)
t = np.linspace(0, 4*np.pi, 500)
r = 3
h = t / 2
x1 = r * np.cos(t)
y1 = r * np.sin(t)
z1 = h

fig = plt.figure(figsize=(6,4))
ax = fig.add_subplot(111, projection='3d')
ax.plot(x1, y1, z1, color='blue', lw=2)
ax.set_title('Drone Path')
plt.savefig("drone_path.png")

# 2. Dome
R = 3
H = 5
theta = np.linspace(0, 2*np.pi, 100)
r = np.linspace(0, R, 50)
r, th = np.meshgrid(r, theta)
x2 = r * np.cos(th)
y2 = r * np.sin(th)
z2 = H * (1 - r**2 / R**2)

fig = plt.figure(figsize=(6,4))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x2, y2, z2, color='orange', alpha=0.8)
ax.set_title('Dome Surface')
plt.savefig("dome_surface.png")

# 3. Terrain (hill and valley)
x = np.linspace(-5, 5, 100)
y = np.linspace(-5, 5, 100)
X, Y = np.meshgrid(x, y)
H = 5; a = 2; k = 3; x0, y0 = 2, 1
Z = H * np.exp(-(X**2 + Y**2)/a**2) - k * np.exp(-((X-x0)**2 + (Y-y0)**2)/1.5**2)

fig = plt.figure(figsize=(6,4))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, cmap='terrain')
ax.set_title('Gaming Terrain')
plt.savefig("terrain.png")


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
