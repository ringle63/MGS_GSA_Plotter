import React from 'react';
import PropTypes from 'prop-types';

const RGLLayout = ({ children }) => {
    return (
        <div
            style={{
                border: '2px solid #4CAF50',
                padding: '10px',
                margin: '10px',
            }}
        >
            {children}
        </div>
    );
};

RGLLayout.propTypes = {
    /**
     * Dash components passed into this layout.
     */
    children: PropTypes.node,
};

export default RGLLayout;