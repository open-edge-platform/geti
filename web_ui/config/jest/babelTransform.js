import babelJest from 'babel-jest';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

export default babelJest.createTransformer({
  presets: [
    [
      require.resolve('babel-preset-react-app'),
      {
        runtime: 'automatic',
      },
    ],
  ],
  babelrc: false,
  configFile: false,
});
