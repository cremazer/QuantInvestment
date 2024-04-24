import numpy as np

# Create a 2-dimensional array
A = np.array([[1, 2], [3, 4]])
print(A)

# View information in an array
print(type(A))

# How many dimensions is the array?
print(A.ndim)

# size of array
print(A.shape)

# data type of elements of array
print(A.dtype)

# Maximum value of each element in an array
print(A.max())

# Average value for each element of the array
print(A.mean())

# Minimum value of each element in an array
print(A.min())

# Sum of elements in array
print(A.sum())

# Indexing Arrays
print(A[0])
print(A[1])

print(A[0][0], A[0][1])
print(A[1][0], A[1][1])

# Output only the elements of array A that are greater than 1
print(A[A > 1])

# Change the shape of an array
print(A.T)
print(A.transpose())

print(A.flatten())

# Array Operations
print(A + A)
print(A - A)
print(A * A)
print(A / A)

# Broadcasting
B = np.array([10, 100])
print(A * B)

# Matrix inner product
print(A.dot(B))