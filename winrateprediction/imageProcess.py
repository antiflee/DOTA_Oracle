import numpy as np
import cv2
import os
from heapq import heappush, heappop

HeroImageFolder = os.path.abspath("./static/winrateprediction/images/.")

def reject_outliers(data, m = 2.):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else 0.
    return data[s<m]

def image_process(img2):
    heroes = [filename for filename in os.listdir(HeroImageFolder) if filename.startswith("120")]
    heroNames=  [hero[6:-4] for hero in heroes]
    coordinates, results, ys = {}, [], []
    num_of_heroes = 10

    img2 = cv2.imread(img2,0)
    sift = cv2.xfeatures2d.SIFT_create()
    kp2, des2 = sift.detectAndCompute(img2,None)
    for hero in heroes:
        img1 = cv2.imread(os.path.join(HeroImageFolder,hero),0)
        kp1, des1 = sift.detectAndCompute(img1,None)

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 3)
        search_params = dict(checks = 100)

        # Create the Flann Matcher object
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1,des2, k=2)
        good = []
        coord = []
        for m,n in matches:
            if m.distance < 0.75*n.distance:
                good.append([m])
                heappush(coord,kp2[m.trainIdx].pt)

        coordinates[hero[6:-4]] = coord
        ys += [y for x,y in coord]

    ys = np.array(ys)
    thres_y = max(reject_outliers(ys))
    results = []
    for name in heroNames:
        sum_x = 0
        i = 0
        while i < len(coordinates[name]):
            coor = coordinates[name][i]
            x,y = coor[0],coor[1]
            if y > thres_y:
                coordinates[name].pop(i)
                continue
            sum_x += x
            i += 1
        if len(coordinates[name]) > 0:
            heappush(results,(len(coordinates[name]),name,sum_x/len(coordinates[name])))
            if len(results) > num_of_heroes:
                heappop(results)

    results.sort(key=lambda x:x[2])
    radiance = [(' ').join(hero.split('-')[0].split('_')) for _,hero,_ in results[:5]]
    dire = [(' ').join(hero.split('-')[0].split('_')) for _,hero,_ in results[5:]]
    print("Radiance: ",radiance, "\nDire: ", dire)
    return radiance, dire
