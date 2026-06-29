# AUTO GENERATED FILE - DO NOT EDIT

export ''_rgllayout

"""
    ''_rgllayout(;kwargs...)
    ''_rgllayout(children::Any;kwargs...)
    ''_rgllayout(children_maker::Function;kwargs...)


A RGLLayout component.

Keyword arguments:
- `children` (a list of or a singular dash component, string or number; optional)
- `id` (String; optional)
- `layout` (Array; optional)
"""
function ''_rgllayout(; kwargs...)
        available_props = Symbol[:children, :id, :layout]
        wild_props = Symbol[]
        return Component("''_rgllayout", "RGLLayout", "dash_rgl", available_props, wild_props; kwargs...)
end

''_rgllayout(children::Any; kwargs...) = ''_rgllayout(;kwargs..., children = children)
''_rgllayout(children_maker::Function; kwargs...) = ''_rgllayout(children_maker(); kwargs...)

