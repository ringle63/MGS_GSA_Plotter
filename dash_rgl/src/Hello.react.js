import React, {Component} from 'react';
import PropTypes from 'prop-types';

class Hello extends Component {
    render() {
        return (
            <div>
                Hello from React! Message: {this.props.message}
            </div>
        );
    }
}

Hello.propTypes = {
    message: PropTypes.string
};

Hello.defaultProps = {
    message: 'Default Message'
};

export default Hello;

/* THIS IS THE IMPORTANT PART */
window.dash_rgl = window.dash_rgl || {};
window.dash_rgl.Hello = Hello;