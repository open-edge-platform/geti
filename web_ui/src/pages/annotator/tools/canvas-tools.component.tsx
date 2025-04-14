// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ToolAnnotationContextProps } from './tools.interface';
import useActiveTool from './use-active-tool';

export const CanvasTools = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const activeTool = useActiveTool(annotationToolContext);

    if (activeTool === undefined) return <></>;

    return <activeTool.Tool annotationToolContext={annotationToolContext} />;
};
