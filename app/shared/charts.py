import json
from wtforms.widgets import HTMLString
from app.shared.colors import Colors, Color


class Dataset():
    def __init__(self, label, data=None):
        self.label = label
        self.data = []

        if data and type(data) == list:
            self.data = data

        self.backgroundColor = []
        self.borderColor = []
        self.borderWidth = 2

    def addData(self, data):
        self.data.append(data)

    def generateColors(self):
        self.backgroundColor = Color.generate(len(self.data), 0.8)

    def generate(self):
        self.generateColors()

        result = {
            'label': self.label,
            'data': self.data,
            'backgroundColor': self.backgroundColor,
            'borderWidth': self.borderWidth
        }

        return result


class Data():
    def __init__(self, labels=None, datasets=None):
        self._labels = []
        self._datasets = []

        if labels:
            if type(labels) != list:
                raise TypeError('labels precisa ser uma lista de strings')
            self._labels = labels

        if datasets:
            if type(datasets) != list and type(datasets[0] != Dataset):
                raise TypeError('datasets precisa ser uma lista de Dataset')
            self._datasets = datasets

    def addDataset(self, dataset):
        if type(dataset) is not Dataset:
            raise TypeError('o objeto precisa ser do tipo Dataset')
        self._datasets.append(dataset)

    def addlabel(self, label):
        if label not in self._labels:
            self._labels.append(str(label))

    def validate(self):
        # Verifica se os labels estão vazios
        if not self._labels:
            raise ValueError('Os labels nao podem estar vazios')
        # Verifica se os datasets estão vazios
        if not self._datasets:
            raise ValueError('Os labels nao podem estar vazios')
        # Verifica se existe labels para todos os datasets
        for dataset in self._datasets:
            if len(dataset.data) != len(self._labels):
                raise Exception('A quantidade de labels deve ser igual a dos dados no datasets')

    def generate(self):
        self.validate()

        result = {
            'labels': self._labels,
            'datasets': [dataset.generate() for dataset in self._datasets]
        }

        result = json.dumps(result)
        return HTMLString(''.join(result))


class BaseChart():

    def __init__(self, title, data=None, option=None, ctype=None, _id=None):
        self._html = []
        self._script = []
        self._data = None
        self._options = {}
        self._options['title'] = {'display': 'true', 'text': title}

        if data and type(data) == Data:
            self._data = data

        self._type = ctype if ctype else 'bar'
        self._id = _id if _id else 'chart-%s' % self._type

    def addData(self, data):
        if type(data) is not Data:
            raise TypeError('o objeto precisa ser do tipo Data')
        self._data = data

    def generateHTML(self):
        self._html.append('<canvas id="%s" width="auto" height="auto"></canvas>' % self._id)
        return HTMLString(''.join(self._html))

    def generateScript(self):
        self._script.append("var ctx = document.getElementById('%s').getContext('2d');" % self._id)
        self._script.append("var barChart = new Chart(ctx, {")
        self._script.append("type: '{}', ".format(self._type))
        self._script.append("data: {}, ".format(self._data.generate()))
        self._script.append("options: {}".format(''.join(map(str, [self._options]))))
        self._script.append('});')

        return HTMLString(''.join(self._script))


class LineChart(BaseChart):
    def __init__(self, title, data=None, option=None, ctype='line', _id=None):
        super(LineChart, self).__init__(title, data=data, option=option, ctype=ctype, _id=_id)
        self._options['elements'] = {'line': {'tension': 0}}
        self._options['tooltipTemplate'] = {'line': {'tension': 0}}



# dataset = Dataset('label', [1, 2, 3])
# data = Data('labels')
# data.addDataset(dataset)
# print(data.generate())

# c = BaseChart(data)
# print(c.generateHTML())
# print(c.generateScript())
