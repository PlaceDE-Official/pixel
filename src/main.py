import numpy as np
import scipy

def getCurrentPixelGoal()->np.ndarray:
    #todo
    #gesendet von redis?
    placeholderGoalArray = np.array([[0, 0, 1, 1],
                                     [0, 0, 1, 1]])
    return placeholderGoalArray

def getCurrentPixelData()->np.ndarray:
    #todo
    #abfrage der daten von influxDB
    placeholderPixelArray = np.array([[0, 0, 0, 1],
                                      [2, 0, 1, 1]])
    return placeholderPixelArray

def raidDetection(diffMap:np.ndarray):
    convolutedDiff = scipy.ndimage.uniform_filter(diffMap, size = 5, mode = "constant", cval = 0)
    pass

def main():
    soll = getCurrentPixelGoal()
    ist = getCurrentPixelData()
    istFiltered = np.where(soll == 0, soll, ist)
    #print(istFiltered)
    diff = np.equal(soll, istFiltered)
    print(diff)
    pass


if __name__ == "__main__":
    main()