import matplotlib.pyplot as plt

# Define the circle parameters
radius = 5
max_axis = 10

# Create a figure and axes
fig, ax = plt.subplots()

# Create a circle patch
circle = plt.Circle((0, 0), radius, color='red')

# Add the circle to the axes
ax.add_patch(circle)

# Set the axis limits
ax.set_xlim([-max_axis, max_axis])
ax.set_ylim([-max_axis, max_axis])

# Set aspect ratio to equal
ax.set_aspect('equal')

# Display the plot
plt.show()