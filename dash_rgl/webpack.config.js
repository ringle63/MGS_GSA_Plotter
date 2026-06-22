const path = require("path");

module.exports = {
    mode: "development",
    entry: "./src/Hello.react.js",

    output: {
        path: path.resolve(__dirname, "dash_rgl"),
        filename: "dash_rgl.min.js",
        library: "dash_rgl",
        libraryTarget: "window"
    },

    externals: {
        react: "React",
        "react-dom": "ReactDOM"
    },

    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: [
                            "@babel/preset-env",
                            "@babel/preset-react"
                        ]
                    }
                }
            }
        ]
    }
};