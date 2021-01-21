import os
import pydicom as pyd
import matplotlib.pyplot as plt

os.chdir('uploaded/')

d0 = pyd.dcmread(os.listdir()[123])

plt.imshow(d0.pixel_array, cmap = 'gray')
plt.show()