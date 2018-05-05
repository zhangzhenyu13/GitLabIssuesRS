'''
this algorithm is aimed at sorting the list obeject under a given constraint
'''
import numpy as np
class XSort:
    def __init__(self,A):
        self.compare_vec_index = -1
        self.A=A
    def compare_list(self,d1,d2):
        index=self.compare_vec_index
        if d1[index]>d2[index]:
            return 1
        elif d1[index]<d2[index]:
            return -1
        else:
            return 0

    #mergeSort
    def merge(self,left,right):
        A=[]
        j=0
        i=0
        while i<len(left) and j<len(right):
            if self.compare_list(left[i],right[j])>=0: # left[i]>=right[j]:
                A.append(left[i])
                i=i+1
            else:
                A.append(right[j])
                j=j+1
        if len(left)>i:
            A=A+left[i:]
        if len(right)>j:
            A=A+right[j:]
        return A
    def mergeSort(self):
        A=self.A
        if len(A)<2:
            return A

        seg=1
        while seg<len(A):
            i=0
            while i<len(A)-seg:
                left=A[i:i+seg]
                right=A[i+seg:i+2*seg]

                A[i:i+2*seg]=self.merge(left,right)
                i=i+2*seg
            seg=seg*2

        return A

#for testing purpose
def main():

    A = [[1, 2], [2, 8], [7, 2], [6, 3],[5,89]]

    mysort=XSort(A)
    mysort.compare_vec_index=-1
    A=mysort.mergeSort()
    A=np.array(A)
    print(A)
    print(A[:,-1])
    print(A[:,-2])

if __name__=="__main__":
    main()