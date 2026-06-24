import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

import GridLayout, {
    WidthProvider,
} from 'react-grid-layout';

const ResponsiveGridLayout =
    WidthProvider(GridLayout);

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';


const RGLLayout = ({
    children,
    layout,
    setProps,
}) => {
    const childArray = React.Children.toArray(children);

    const defaultLayout = childArray.map((_, i) => ({
        i: String(i),
        x: 0,
        y: i * 4,
        w: 10,
        h: 8,
    }));

    const [currentLayout, setCurrentLayout] = useState(defaultLayout);

    useEffect(() => {

        // Panel added
        if (childArray.length > currentLayout.length) {

            const newLayout = [...currentLayout];

            for (let i = currentLayout.length; i < childArray.length; i++) {
                newLayout.push({
                    i: String(i),
                    x: 0,
                    y: Infinity,
                    w: 10,
                    h: 8,
                });
            }

            setCurrentLayout(newLayout);
            return;
        }

        // Panel removed
        if (childArray.length < currentLayout.length) {

            setCurrentLayout(
                currentLayout.slice(0, childArray.length)
            );
        }

    }, [childArray.length]);

    return (
        <ResponsiveGridLayout
            className="layout"
            layout={currentLayout}
            cols={36}
            rowHeight={40}
            onResizeStop={() => {
                document
                    .querySelectorAll('.js-plotly-plot')
                    .forEach(g => {
                        if (window.Plotly) {
                            window.Plotly.Plots.resize(g);
                        }
                    });
            }}
            onDragStop={() => {
                document
                    .querySelectorAll('.js-plotly-plot')
                    .forEach(g => {
                        if (window.Plotly) {
                            window.Plotly.Plots.resize(g);
                        }
                    });
            }}
            style={{
                minWidth: '100%',
                width: '300%',
            }}
            measureBeforeMount={false}
            isResizable={true}
            isDraggable={true}
            draggableHandle=".react-grid-dragHandle"

            onLayoutChange={(newLayout) => {
                setCurrentLayout(newLayout);

                window.dispatchEvent(
                    new Event('resize')
                );

                if (setProps) {
                    setProps({
                        layout: newLayout,
                    });
                }
            }}
        >
            {childArray.map((child, i) => (
                <div
                    key={String(i)}
                    style={{
                        backgroundColor: 'white',
                        border: '2px solid #4CAF50',
                        overflow: 'hidden',
                        display: 'flex',
                        flexDirection: 'column',
                        minWidth: 0,
                    }}
                >
                    <div
                        className="react-grid-dragHandle"
                        style={{
                            backgroundColor: '#dddddd',
                            padding: '8px',
                            cursor: 'move',
                            fontWeight: 'bold',
                            flexShrink: 0,
                        }}
                    >
                        Panel {i + 1}
                    </div>

                    <div
                        style={{
                            flex: 1,
                            overflow: 'auto',
                            padding: '8px',
                            minWidth: 0,
                            minHeight: 0,
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                        }}
                    >
                        {child}
                    </div>
                </div>
            ))}
        </ResponsiveGridLayout>
    );
};


RGLLayout.propTypes = {
    id: PropTypes.string,

    children: PropTypes.node,

    layout: PropTypes.array,

    setProps: PropTypes.func,
};


export default RGLLayout;