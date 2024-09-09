import matplotlib.pyplot as plt

# Define the square's coordinates
x = [0, 5, 5, 0, 0]  # x-coordinates of the square's vertices
y = [0, 0, 5, 5, 0]  # y-coordinates of the square's vertices

# Plot the square
plt.plot(x, y, 'r-', linewidth=2)  # Plot the square with a red line

# Set axis limits and labels
plt.xlim(-1, 6)  # Set x-axis limits
plt.ylim(-1, 6)  # Set y-axis limits
plt.xlabel('X')  # Label the x-axis
plt.ylabel('Y')  # Label the y-axis

# Display the plot
plt.show()