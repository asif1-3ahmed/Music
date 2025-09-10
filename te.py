arr = [10, 20, 30, 40, 50, 60, 70]
target = 50
print("Binary Search Result:", binary_search(arr, target))

def interpolation_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high and arr[low] <= target <= arr[high]:
        
        pos = low + ((target - arr[low]) * (high - low) // (arr[high] - arr[low]))

        if arr[pos] == target:
            return pos   
        elif target < arr[pos]:
            high = pos - 1   
        else:
            low = pos + 1    

    return -1  



arr = [10, 20, 30, 40, 50, 60, 70]
target = 50
print("Interpolation Search Result:", interpolation_search(arr, target))
