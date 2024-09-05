import matplotlib.pyplot as plt
import numpy as np

# Create a circle with radius 5
radius = 5
x = np.linspace(-radius, radius, 100)
y = np.sqrt(radius**2 - x**2)

# Plot the circle
plt.plot(x, y, color='red')
plt.plot(x, -y, color='red')

# Set axis limits
plt.xlim(-10, 10)  # Maximum axis of 10
plt.ylim(-10, 10)

# Remove axes
plt.axis('off')

# Display the plot
plt.show()