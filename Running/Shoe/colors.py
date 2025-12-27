import colorsys

def generate_distinct_colors(num_colors):
    colors = []
    for i in range(num_colors):
        hue = (i * 137.508) % 360  # Using the golden angle to spread out hues
        rgb = colorsys.hsv_to_rgb(hue / 360, 0.7, 0.9)  # HSV values for color
        hex_color = "#{:02X}{:02X}{:02X}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        colors.append(hex_color)
    return colors

# Generate 100 distinct colors
distinct_colors = generate_distinct_colors(100)

# Print the list of colors
print(distinct_colors)
