import cv2 as cv
import numpy as np


class DefectComparison(object):
    """docstring for DefectComparison"""

    def __init__(self, ptdic, shape, picpath, resizedef):
        super(DefectComparison, self).__init__()
        self.ptdic = ptdic
        self.shape = shape
        self.pic = cv.imread(picpath)
        self.resizedef = resizedef

    def getone(self, n, shape, hov):
        # 防止Main匹配时切图切片值比图片像素大而返回空图
        if n < 0:
            return 0
        else:
            if not hov:
                if n > shape[1]:
                    return shape[1]
                else:
                    return n
            else:
                if n > shape[0]:
                    return shape[0]
                else:
                    return n

    def getOverlapping(self, ptss, target):
        # 零件的匹配，矩阵相加进行匹配
        im1 = np.zeros(self.shape[:2], dtype=np.uint8)
        for pts in ptss:
            im1 = cv.fillConvexPoly(im1, pts, 1)

        if not isinstance(target, np.ndarray):
            target = self.pic // 255
            target = self.resizedef(target)
        else:
            im2 = np.zeros(self.shape[:2], dtype=np.uint8)
            target = cv.fillConvexPoly(im2, target, 1)

        img = im1 + target

        if (img > 1).any():
            return 1
        else:
            return 0

    def getMOverlapping(self, m, target):
        # 进行piex个数的匹配，将图片一个piex一个piex的切开，故障同理然后匹配，快
        sum_m = 0

        im1 = np.ones(self.shape[:2], dtype=np.uint8)

        if not isinstance(target, np.ndarray):
            target = self.pic // 255
            target = self.resizedef(target)
        else:
            im2 = np.zeros(self.shape[:2], dtype=np.uint8)
            target = cv.fillConvexPoly(im2, target, 1)

        for p in m:
            v1 = self.getone(p[0][1], self.shape, 1)
            v2 = self.getone(p[2][1], self.shape, 1)
            if v1 > v2:
                v1, v2 = v2, v1
            h1 = self.getone(p[0][0], self.shape, 0)
            h2 = self.getone(p[2][0], self.shape, 0)
            if h1 > h2:
                h1, h2 = h2, h1

            im = im1[v1:v2, h1:h2]

            tr = target[v1:v2, h1:h2]

            get = im + tr

            if (get > 1).any():
                sum_m += 1

        return sum_m

    def getReturn(self, m1, m2, m):
        # 返回最终要求的result，自行定义
        result = {}
        result['AFFECTEDPIXELNUM'] = m
        if not m1:
            result['ISM1OPEN'] = False
            result['M1M1'] = False
        else:
            result['ISM1OPEN'] = True
            if m1 > 1:
                result['M1M1'] = True
            else:
                result['M1M1'] = False
        if not m2:
            result['ISM2OPEN'] = False
            result['M2M2'] = False
        else:
            result['ISM2OPEN'] = True
            if m2 > 1:
                result['M2M2'] = True
            else:
                result['M2M2'] = False
        if m1 > 0 and m2 > 0:
            result['M1M2'] = True
        else:
            result['M1M2'] = False
        return result

    def getQOut(self, target=0):
        # 与m1相加个数，m2相交个数，影响了几个piex
        sum_m1 = 0
        sum_m2 = 0
        sum_m = 0

        # 一组一组与故障匹配，如果不要求故障个数可以将m1放在循环外，一次性匹配更快，m2同理
        for i in range(len(self.ptdic['Main'])):
            m1 = []
            # 将一组零件放入一个list
            for key in ['M1-1', 'M1-2', 'M1-3']:
                m1.append(self.ptdic[key][i])
            # 匹配故障
            if self.getOverlapping(m1, target):
                sum_m1 += 1

        for i in range(len(self.ptdic['Main'])):
            m2 = []
            for key in ['M2-1', 'M2-2', 'M2-3']:
                m2.append(self.ptdic[key][i])
            if self.getOverlapping(m2, target):
                sum_m2 += 1

        # 计算piex的思路不同，是把所有main放入一个list，然后切块匹配
        m = []
        for i in range(len(self.ptdic['Main'])):
            for key in ['Main']:
                m.append(self.ptdic[key][i])
        sum_m = self.getMOverlapping(m, target)

        return self.getReturn(sum_m1, sum_m2, sum_m)
