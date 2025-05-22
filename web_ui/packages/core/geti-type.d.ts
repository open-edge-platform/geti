// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/// <reference types="@rsbuild/core/types" />

/*
    TODO: We can remove it once @geti/core does not have any dependencies in the main geti
 */

declare module '*.svg' {
    export const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
}
declare module '*.svg?react' {
    const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
    export default ReactComponent;
}
