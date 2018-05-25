import abc
from wtforms.widgets import html_params, HTMLString


class GeBaseWidget(abc.ABC):

    html_params = staticmethod(html_params)
    input_mask = None

    def __init__(self, input_type=None):
        if input_type is not None:
            self.input_type = input_type

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        self.inputId = kwargs.get('id', field.id)

        if field.flags.required:
            self.html = [u'<div class="form-group required">']
        else:
            self.html = [u'<div class="form-group">']

        # Define o label do campo
        self.html.append(
            u'<label class="control-label" for="%s">' % (self.inputId)
        )
        self.html.append(u'%s' % field.label)
        self.html.append(u'</label>')

        if 'value' not in kwargs:
            v = getattr(field, '_value', None)
            if v:
                kwargs['value'] = v()

        self._createInput(field, **kwargs)

        self.html.append(u'</div>')

        return HTMLString(''.join(self.html))

    @abc.abstractmethod
    def _createInput(self):
        pass


class GeSelectMultipleWidget(GeBaseWidget):

    input_type = 'text'

    def __call__(self, field, **kwargs):
        return super(GeSelectMultipleWidget, self).__call__(field, **kwargs)

    def _createInput(self, field, **kwargs):
        required = 'required' if field.flags.required else ''
        
        self.html.append(
            u'<select multiple class="form-control" {}>'.format(
                self.html_params(
                    name=field.name,
                    id=self.inputId,
                    required=required
                )
            )
        )
        
        for value, label, selected in field.iter_choices():
            options = dict(value=value)
            
            if selected:
                options['selected'] = 'selected'
            
            self.html.append(
                u'<option {}>{}</option>'.format(
                    self.html_params(**options), 
                    label
                )
            )
        
        self.html.append(u'</select>')
