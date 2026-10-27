import scipy.stats as stats
import numpy as np

observed = np.array([[145, 55], [120, 80]])
chi2, p, dof, expected = stats.chi2_contingency(observed)

print("Chi-square:", chi2)
print("p-value:", p)
print("Degrees of freedom:", dof)
print("Expected frequencies:\n", expected)
