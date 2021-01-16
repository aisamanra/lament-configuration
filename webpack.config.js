const path = require('path');

module.exports = {
    entry: path.resolve(__dirname, 'js', 'index.js'),
    output: {
        path: path.resolve(__dirname, 'static'),
        filename: 'lc.js'
    },
    resolve: {
        extensions: ['.js', '.jsx']
    },
    module: {
        rules: [
            {
                test: /\.jsx/,
                use: {
                    loader: 'babel-loader',
                    options: { presets: ['@babel/preset-react', '@babel/preset-env'] }
                }
            }
        ]
    }
};
