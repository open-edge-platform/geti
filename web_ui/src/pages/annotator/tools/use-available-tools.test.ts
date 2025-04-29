// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { ToolType } from '../core/annotation-tool-context.interface';
import { useAvailableTools } from './use-available-tools.hook';

describe('useAvailableTools', () => {
    it('includes segment anything', () => {
        const { result } = renderHook(() => useAvailableTools([DOMAIN.SEGMENTATION]));

        expect(result.current.some((tool) => tool.type === ToolType.SegmentAnythingTool)).toBeTruthy();
    });
});
