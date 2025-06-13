// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/// <reference types="@rsbuild/core/types" />

/**
 * The BeforeInstallPromptEvent is fired at the Window.onbeforeinstallprompt handler
 * before a user is prompted to "install" a web site to a home screen on mobile.
 *
 * @deprecated Only supported on Chrome and Android Webview.
 */
declare interface BeforeInstallPromptEvent extends Event {
    /**
     * Returns an array of DOMString items containing the platforms on which the event was dispatched.
     * This is provided for user agents that want to present a choice of versions to the user such as,
     * for example, "web" or "play" which would allow the user to chose between a web version or
     * an Android version.
     */
    readonly platforms: Array<string>;

    /**
     * Returns a Promise that resolves to a DOMString containing either "accepted" or "dismissed".
     */
    readonly userChoice: Promise<{
        outcome: 'accepted' | 'dismissed';
        platform: string;
    }>;

    /**
     * Allows a developer to show the installation prompt at a time of their own choosing.
     * This method returns a Promise.
     */
    prompt(): Promise<void>;
}

declare interface WindowEventHandlersEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
}

declare module 'OpenCVTypes' {
    import * as OpenCVTypes from '@geti/smart-tools/opencv';

    export = OpenCVTypes;
}

declare const cv: Promise<OpenCVTypes.cv>;

declare module 'opencv' {
    import OpenCVTypes from '@geti/smart-tools/opencv';

    const OpenCV: Promise<OpenCVTypes>;
    export default OpenCV;
}

// We need these two to be able to import/export svgs as ReactComponent,
// for instance: export { ReactComponent as Logo } from './logo.svg';
declare module '*.svg' {
    export const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
}
declare module '*.svg?react' {
    const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
    export default ReactComponent;
}

declare module '*.pdf';
