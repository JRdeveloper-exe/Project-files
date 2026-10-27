import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

# Data
experience = np.array([1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 16, 18, 20])
education = np.array([0, 0, 1, 1, 0, 2, 1, 2, 1, 2, 0, 1, 2, 0, 1])
location = np.array([0, 1, 1, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 0, 1])
salary = np.array([48, 53, 60, 65, 68, 80, 78, 88, 90, 100, 92, 105, 108, 115, 120])

# -------------------------------
# 1. Scatter plot: Experience vs Salary
# -------------------------------
colors = ['red', 'green', 'blue']  # Remote, On-site, Hybrid
markers = ['o', 's', '^']          # Bachelor's, Master's, PhD

plt.figure(figsize=(10, 6))
for i in range(len(experience)):
    plt.scatter(experience[i], salary[i],
                color=colors[location[i]],
                marker=markers[education[i]],
                s=100,
                label=f"Loc {location[i]} Edu {education[i]}" if i == 0 else "")

plt.title("Experience vs Salary (Color=Location, Shape=Education)")
plt.xlabel("Years of Experience")
plt.ylabel("Salary (USD thousands)")
plt.grid(True)

# -------------------------------
# 2. Lines of best fit per location
# -------------------------------
for loc in [0, 1, 2]:
    mask = location == loc
    X_loc = experience[mask].reshape(-1, 1)
    y_loc = salary[mask]
    model = LinearRegression().fit(X_loc, y_loc)
    x_range = np.linspace(min(X_loc), max(X_loc), 100).reshape(-1, 1)
    y_pred = model.predict(x_range)
    plt.plot(x_range, y_pred, label=f"Location {loc} Fit", linestyle='--')

plt.legend()
plt.show()

# -------------------------------
# 3. Multiple Linear Regression
# -------------------------------
# Features: Experience, Experience², Education, Location
X = np.column_stack((experience, experience**2, education, location))
y = salary

reg = LinearRegression().fit(X, y)
print("Model Coefficients:", reg.coef_)
print("Intercept:", reg.intercept_)

# -------------------------------
# 4. Predictions
# -------------------------------
# A: 9 years, Master's (1), Remote (0)
X_pred1 = np.array([[9, 81, 1, 0]])
pred1 = reg.predict(X_pred1)[0]

# B: 14 years, PhD (2), Hybrid (2)
X_pred2 = np.array([[14, 196, 2, 2]])
pred2 = reg.predict(X_pred2)[0]

print(f"\nPredicted Salary A: ${pred1:.2f}K")
print(f"Predicted Salary B: ${pred2:.2f}K")

# -------------------------------
# 5. Combined Graph with Predictions
# -------------------------------
plt.figure(figsize=(10, 6))
for i in range(len(experience)):
    plt.scatter(experience[i], salary[i],
                color=colors[location[i]],
                marker=markers[education[i]],
                s=100)

# Add predicted points
plt.scatter(9, pred1, color='black', marker='*', s=200, label="Predicted A")
plt.scatter(14, pred2, color='purple', marker='*', s=200, label="Predicted B")

# Add best fit lines again
for loc in [0, 1, 2]:
    mask = location == loc
    X_loc = experience[mask].reshape(-1, 1)
    y_loc = salary[mask]
    model = LinearRegression().fit(X_loc, y_loc)
    x_range = np.linspace(min(X_loc), max(X_loc), 100).reshape(-1, 1)
    y_pred = model.predict(x_range)
    plt.plot(x_range, y_pred, label=f"Location {loc} Fit", linestyle='--')

plt.title("Combined Salary Analysis")
plt.xlabel("Years of Experience")
plt.ylabel("Salary (USD thousands)")
plt.legend()
plt.grid(True)
plt.show()
