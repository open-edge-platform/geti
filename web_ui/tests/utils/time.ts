// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const getMockDateScript = (time: number) => `{
    Date = class extends Date {
      constructor(...args) {
        if (args.length === 0) {
          super(${time});
        } else {
          super(...args);
        }
      }
    }

    const __DateNowOffset = ${time} - Date.now();
    const __DateNow = Date.now;
    Date.now = () => __DateNow() + __DateNowOffset;
  }`;
