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
        y: i * 2,
        w: 12,
        h: 2,
    }));

    return (
        <GridLayout
            className="layout"
            cols={12}
            rowHeight={30}
            width={1200}
            isResizable={true}
            isDraggable={true}
            draggableHandle=".react-grid-dragHandle"
        >
        <div key="0">
            <div
                className="react-grid-dragHandle"
                style={{
                    background: '#cccccc',
                    padding: '6px',
                    cursor: 'move',
                    fontWeight: 'bold',
                }}
            >
                Drag Me
            </div>

            <div
                style={{
                    border: '2px solid red',
                    background: '#eeeeee',
                    height: '100%',
                }}
            >
                TEST 1
            </div>
        </div>

            <div key="1">
                <div
                    className="react-grid-dragHandle"
                    style={{
                        background: '#cccccc',
                        padding: '6px',
                        cursor: 'move',
                        fontWeight: 'bold',
                    }}
                >
                    Drag Me
                </div>

                <div
                    style={{
                        border: '2px solid blue',
                        background: '#dddddd',
                        height: '100%',
                    }}
                >
                    TEST 2
                </div>
            </div>
        </GridLayout>
    );
};


RGLLayout.propTypes = {
    /**
     * Dash components passed into this layout.
     */
    children: PropTypes.node,
};


export default RGLLayout;