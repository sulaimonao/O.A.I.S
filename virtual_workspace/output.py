import matplotlib.pyplot as plt
import numpy as np

# Define the circle parameters
radius = 5
max_axis = 10

# Create a circle with the given radius
theta = np.linspace(0, 2*np.pi, 100)
x = radius * np.cos(theta)
y = radius * np.sin(theta)

# Plot the circle
plt.plot(x, y, color='red', linewidth=2)

# Set the axes limits
plt.xlim(-max_axis, max_axis)
plt.ylim(-max_axis, max_axis)

# Remove the axes ticks and labels
plt.xticks([])
plt.yticks([])

# Show the plot
plt.show()