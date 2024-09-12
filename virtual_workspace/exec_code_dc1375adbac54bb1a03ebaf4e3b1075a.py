import matplotlib.pyplot as plt

# Define the circle parameters
radius = 5
center_x = 0
center_y = 0

# Create a figure and axes
fig, ax = plt.subplots()

# Create a circle patch
circle = plt.Circle((center_x, center_y), radius, color='red')

# Add the circle to the axes
ax.add_patch(circle)

# Set the axis limits
ax.set_xlim(-radius-1, radius+1)
ax.set_ylim(-radius-1, radius+1)

# Remove the axis ticks and labels
ax.set_xticks([])
ax.set_yticks([])

# Save the figure as a PNG file
plt.savefig("solid_red_circle.png")

# Show the plot (optional)
plt.show()