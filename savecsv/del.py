import sys

weights = [45,25,10,5,2.5]
ret = []
def findPlates(weight, barWeight):
    weight -= barWeight
    for plate in weights:
        pairWeight = plate*2
        while weight > pairWeight:
            ret.append(plate)
            weight -= pairWeight
    return ret

if __name__ == "__main__":
   print(findPlates(int(sys.argv[1]), int(sys.argv[2])))