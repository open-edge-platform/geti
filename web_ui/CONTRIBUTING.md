# Contributing to Intel Geti Web UI

**Prerequisites**: We recommend developing Geti's UI locally using node v22.12.0 and npm v10.9.0. You will also need to have a Geti server available. Please see our [documentation]() for instructions to install Geti on your hardware.

## Local Setup with npm 

To get started with contributing to the UI first install all node dependencies locally

```sh
web_ui/ $ npm ci
```
## Setting up environment variables

Duplicate .env.example file and rename it to .env
Next make a `.env` file that includes a `REACT_APP_API_PROXY` variable, you copy over the `.env.example` file,
```sh
web_ui/ $ cp .env.example .env
```

Our proxy will redirect all `/api` requests  to `localhost:80/api` assuming your `REACT_APP_API_PROXY` is set to `localhost:80`. Update this variable with your server address/
Assuming you have your Geti server running on `localhost:80` you are now all set to start changing the Geti UI.
Start up the [Rsbuild](https://rsbuild.dev/) dev server with,

```sh
web_ui/ $ npm run start
```

The project should now load correctly.

Keep reading to learn more about our linting and testing setup.

## Testing and Quality Control

We heavily rely on Typescript, ESLint, Jest and Playwright to make sure we don't introduce regressions as well as to help us improve the design of our code.

### Typescript

```sh
npm run test:tsc
```

Checks if there are no typescript violations. We have a relatively strict typescript configuration and also use `typescript-eslint` for some additional safeguards.

### Check lint rules

```sh
npm run test:eslint
npm run test:eslint:fix
```

Our CI uses `npm run test:eslint` to verify that no eslint rules are violated. For development we often use `npm run test:eslint:fix` to automatically fix these where possible.

#### Cyclic dependencies

In the past we've had issues where cyclic dependencies introduced build regressions, this is why we added an additional step in our CI to check for this.

```sh
npm run cyclic-deps-check
```

### Formatting with prettier

We use prettier to automatically format our code,

```
npm run format:check
npm run format
```

Note that `npm run format` will both check and fix any formatting issues.

### Unit testing

```sh
npm run test:unit
npm run test:unit:watch
```

Use the watch command to interactively choose the unit tests you want to run while making code changes.
Depending on your machine's memory and cpu you may want to add a `--maxWorkers` to prevent jest from using up all your system's resources,

```sh
npm run test:unit:watch -- --maxWorkers=4
```

### Component testing

We rely on [Playwright](https://playwright.dev/) for our component tests. 
There are two ways with which you can run these: using a dev server with HRM or using a build server without HRM which tends to make the component tests run be faster, with the caveat that you will need to rebuild the UI files whenever you make a change,

1. **Dev Server**: First we start up a dev server,

```sh
npm run start
```

2. **Build server**:

  Build both the Geti app and the Admin app,

```sh
npm run build:all-routes
```

  Next use the preview command to start a server,
  
```sh
npm run preview -- --environment=dev
```

  This will start up a server without Hot Module Reloading, which typically makes the component tests run faster.
  

Next you can run the component tests with,

```sh
npm run test:component
```

Or if you prefer using Playwright's [UI mode](https://playwright.dev/docs/test-ui-mode) you can use
  
```sh
npm run test:component:ui
```

#### Useful third party tools

https://github.com/ruifigueira/playwright-crx

### Finding deadcode

We use [knip.dev](https://knip.dev/) to find and remove code that is no longer being used.

```sh
npm run find-deadcode
```
