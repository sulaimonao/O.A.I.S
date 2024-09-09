import matplotlib.pyplot as plt

# Define circle parameters
radius = 5
center_x = 0
center_y = 0

# Create a circle using matplotlib.patches.Circle
circle = plt.Circle((center_x, center_y), radius, color='red')

# Create a figure and axes
fig, ax = plt.subplots()

# Add the circle to the axes
ax.add_patch(circle)

# Set the axis limits
ax.set_xlim(-radius - 1, radius + 1)
ax.set_ylim(-radius - 1, radius + 1)

# Set aspect ratio to equal to ensure the circle appears circular
ax.set_aspect('equal')

# Show the plot
plt.show()