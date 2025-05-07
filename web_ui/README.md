# Getting Started with the Intel Geti Web UI

Welcome to Intel Geti Web UI. This document aims to explain the high level architecture of our application, starting with our core stack: React, Typescript and Rsbuild.
For a full deep dive visit our developer documentation [`here`](https://docs.geti.intel.com/developer-guide/interactive-ai/frontend/).

## Application structure

The web UI of Geti is a Single Page Application utilizing [react router](https://reactrouter.com/) for client side routing. [Rsbuild](https://rsbuild.dev) is our build tool.
Below is a diagram of our route structure,

<center>

![geti-route-structure](https://github.com/user-attachments/assets/d32a2a62-183a-4b06-a1b7-f69da007893a)

</center>

The `intel-admin` routes are used to manage organizations and users as well as assigning credits. These routese are used by the [admin environment](https://github.com/open-edge-platform/geti/blob/7e46430b7afeca6288f7e751d49adacac61fd7f3/web_ui/rsbuild.config.ts#L66-L77) while the other routes are used by the [geti environment](https://github.com/open-edge-platform/geti/blob/7e46430b7afeca6288f7e751d49adacac61fd7f3/web_ui/rsbuild.config.ts#L53-L65).
The admin environment isn't available via our installer or helm chart instructions, this will likely change in the future.

Keep reading to get an overview of our core architecture, stack, testing strategies and usage of client side computer vision algorithms to speed up annotation time.

## Architecture 

- **Core stack**: Our UI is a React application build using Rsbuild & npm. Typescript is our language of choice.
- **Application**: React Router and TanStack Query are critical for managing navigation and data fetching efficiently in our application.
- **Testing**: we aim to have a high code coverage where we use jest for unit tests and Playwright for our component and end-to-end tests.
- **Algorithms & AI**: Our UI contains smart annotation tools that speed up annotation efforts. We use [OpenCV](https://opencv.org/), [OnnxRUntime](https://onnxruntime.ai) compiled to [WebAssembly](https://webassembly.org/) and use [WebWorkers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers) to make sure heavy computations don't block the UI thread.

---

### Core stack

| ![npm](./npm.png) | ![Typescript](./typescript.png) | ![React](./react.png) | ![Rsbuild](./rsbuild.png) |
|-------------------|---------------------------------|-----------------------|---------------------------|

Our core architecture consists of using [npm](https://www.npmjs.com/) as our package manager, [Typescript](https://www.typescriptlang.org/) as the language of choice and [react](react.dev) as our frontend framework.

Initially the UI was build from [Create React App](https://github.com/facebook/create-react-app). Which we then migrated since to [rsbuild](https://rsbuild.dev/). 
Thanks to Rspack, Rsbuild allows us to have lightning fast builds and provides consistency between development and production. See [Rsbuild's comparisons](https://rsbuild.dev/guide/start/#-comparisons) for more info.

### Application

| ![React Router](./react-router.png) | ![Tanstack Query](./tanstack-query.png) | ![Adobe Spectrum](./adobe-spectrum.png) |
|-------------------------------------|-----------------------------------------|-----------------------------------------|

- **Routing & Navigation**: React Router manages client-side routing. We currently only use it for client side navigation, but are looking into integrating data loaders to speedup initial page loads.
- **Data & State**: TanStack Query is used for server state, e.g. data fetching and other async processes. 
- **UI Components**: We use Adobe's [React Spectrum](https://react-spectrum.adobe.com/) as our UI component library. Custom components often use [React Aria](https://react-spectrum.adobe.com/react-aria/index.html) either as hooks or via react-aria-components and are styled via css modules.

### Testing

| ![Testing Library](./testing-library.png) | ![Jest](./jest.png) | ![Playwright](./playwright.png) |
|-------------------------------------------|---------------------|---------------------------------|


- **Avoiding a test user**: We use [Testing Library](https://testing-library.com/)'s interfaces both in our unit and component/e2e tests. This allows us to avoid having a [testing user](https://kentcdodds.com/blog/avoid-the-test-user). This also aligns well with React Aria's focus on accessibility.
- **Unit tests**: We use [jest](https://jestjs.io/) as our unit testing framework.
- **Playwright**: Our component (isolated UI browser tests that rely on a mocked backend) and End-to-End (No mocking, tests are run on an actual server) use [Playwright](https://playwright.dev/)

### Algorithms & AI

| ![WebAssembly](./web-assembly.png) | ![OpenCV](./open-cv.png) | ![ONNXRuntime](./onnx-runtime.png) | ![Web Workers](./web-workers.png) |
|------------------------------------|--------------------------|------------------------------------|------------------------------------|

Our annotator contains smart tools such as [Detection Assistant](https://docs.geti.intel.com/docs/user-guide/geti-fundamentals/annotations/annotation-tools#detection-assistant-tool) or [Automatic Segmentation](https://docs.geti.intel.com/docs/user-guide/geti-fundamentals/annotations/annotation-tools#automatic-segmentation-tool) are local only and rely on [Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers) to keep the UI smooth and non blocking when we are performing heavy compute.
The tools are implemented using [OpenCV](https://opencv.org/), [OnnxRUntime](https://onnxruntime.ai) compiled to [WebAssembly](https://webassembly.org/).

