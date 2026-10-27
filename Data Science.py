import numpy as np
DS = [6532, 8741, 5403, 7829, 9126, 6087, 7324, 8560, 5972, 7645, 6891, 8102, 7456, 
6213, 9034]
#Now we  are writing a code to organize the data
sorted_DS = sorted(DS, reverse=True)
print("Original Daily Steps: ",DS)
print(" ")
print("Daily Steps in decending order: ",sorted_DS)

#Now we are writing a code for ther calculation for mean, standard deviation
DS_mean = np.mean(DS)
std_DS = np.std(DS)
#code for rounding off
DS_mean = round(DS_mean)
std_DS = round(std_DS)
#Printing all  the results 
print(" ")
print("This is the mean of the data: ", DS_mean)
print(" ")
print("This is the Standard Deviation of the data: ", std_DS)
# Calculating percentiles
per25 = np.percentile(DS, 25)
per50 = np.percentile(DS, 50)
per75 = np.percentile(DS, 75)
# Displaying the results
print(" ")
print("25th Percentile: ", per25)
print(" ")
print("Median: ", per50)
print(" ")
print("75th Percentile: ", per75)


