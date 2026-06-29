# AUTO GENERATED FILE - DO NOT EDIT

#' @export
''RGLLayout <- function(children=NULL, id=NULL, layout=NULL) {
    
    props <- list(children=children, id=id, layout=layout)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'RGLLayout',
        namespace = 'dash_rgl',
        propNames = c('children', 'id', 'layout'),
        package = 'dashRgl'
        )

    structure(component, class = c('dash_component', 'list'))
}
