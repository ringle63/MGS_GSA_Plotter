# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args
try:
    from dash.types import NumberType  # noqa: F401
except ImportError:
    # Backwards compatibility for dash<=4.1.0
    if typing.TYPE_CHECKING:
        raise
    NumberType = typing.Union[  # noqa: F401
        typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
    ]

ComponentSingleType = typing.Union[str, int, float, Component, None]
ComponentType = typing.Union[
    ComponentSingleType,
    typing.Sequence[ComponentSingleType],
]


class RGLLayout(Component):
    """A RGLLayout component.
ExampleComponent is an example component.
It takes a property, `label`, and
displays it.
It renders an input with the property `value`
which is editable by the user.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- label (string; required):
    A label that will be printed when this component is rendered.

- value (string; optional):
    The value displayed in the input."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_rgl'
    _type = 'RGLLayout'


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        label: typing.Optional[str] = None,
        value: typing.Optional[str] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'label', 'value']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'label', 'value']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        for k in ['label']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        super(RGLLayout, self).__init__(**args)

setattr(RGLLayout, "__init__", _explicitize_args(RGLLayout.__init__))
