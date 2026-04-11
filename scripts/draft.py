import numpy as np

ll = np.random.randint(-10, 10, size=30).tolist()
print(ll)
mm = [m + 1000 for m in ll if m > 6]
print(mm)