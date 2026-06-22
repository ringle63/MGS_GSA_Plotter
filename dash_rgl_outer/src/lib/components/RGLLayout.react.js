import React from 'react';
import PropTypes from 'prop-types';

import GridLayout from 'react-grid-layout';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';


const RGLLayout = ({ children }) => {
    const childArray = React.Children.toArray(children);

    const layout = childArray.map((_, i) => ({
        i: String(i),
        x: 0,
        y: i * 4,
        w: 12,
        h: 8,
    }));

    return (
        <GridLayout
            className="layout"
            layout={layout}
            cols={12}
            rowHeight={40}
            width={1200}
            isResizable={true}
            isDraggable={true}
            draggableHandle=".react-grid-dragHandle"
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
                        }}
                    >
                        {child}
                    </div>
                </div>
            ))}
        </GridLayout>
    );
};


RGLLayout.propTypes = {
    id: PropTypes.string,
    children: PropTypes.node,
};


export default RGLLayout;