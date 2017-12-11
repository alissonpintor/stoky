from enum import Enum
import random as r


class Color():
    @staticmethod
    def generate(max, alpha):
        colors = []
        for x in range(max):
            rgba = 'rgba('
            rgba = rgba + str(r.randint(155, 255)) + ','
            rgba = rgba + str(r.randint(155, 255)) + ','
            rgba = rgba + str(r.randint(155, 255)) + ','
            rgba = rgba + str(alpha) + ')'
            colors.append(rgba)
        return colors


class Colors(Enum):
    RED = ['rgba(%i, 0, 0, 0.8)' % x for x in range(255, 10, -50)]




'''
    backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
                'rgba(153, 102, 255, 0.2)',
                '#fff'
            ],
            borderColor: [
                'rgba(255,99,132,1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ]
'''
